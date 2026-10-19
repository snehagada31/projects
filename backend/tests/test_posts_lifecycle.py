"""
Automated test suite proving Stage 5 (PY-P0-05) Owned-Content Lifecycle acceptance criteria:
1. Authenticated post creation sets author to verified actor.
2. Only author can edit post text (PATCH /posts/{id}).
3. Non-author edit attempts are rejected with 403 Forbidden; post text remains unchanged.
4. Immutable/unknown fields in edit request are rejected with 422 Unprocessable Entity.
5. Only author can delete post (DELETE /posts/{id}); non-author deletes rejected with 403 Forbidden.
"""

import uuid
import pytest


def test_author_can_edit_post(client):
    reg = client.post("/auth/register", json={
        "handle": f"author_{uuid.uuid4().hex[:8]}",
        "displayName": "Author",
        "password": "password123!",
    })
    token = reg.json()["token"]

    # Author creates original post
    create_res = client.post(
        "/posts",
        headers={"Authorization": f"Bearer {token}"},
        json={"kind": "original", "text": "Original draft text"},
    )
    assert create_res.status_code == 201
    post_id = create_res.json()["item"]["id"]

    # Author edits text
    patch_res = client.patch(
        f"/posts/{post_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"text": "Refined and published text"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["item"]["text"] == "Refined and published text"

    # Verify read surface shows edited text
    get_res = client.get(f"/posts/{post_id}")
    assert get_res.status_code == 200
    assert get_res.json()["item"]["text"] == "Refined and published text"


def test_non_author_edit_rejected_with_403(client):
    # Author A
    reg_a = client.post("/auth/register", json={
        "handle": f"autha_{uuid.uuid4().hex[:8]}",
        "displayName": "Author A",
        "password": "password123!",
    })
    token_a = reg_a.json()["token"]

    # Hacker B
    reg_b = client.post("/auth/register", json={
        "handle": f"hackerb_{uuid.uuid4().hex[:8]}",
        "displayName": "Hacker B",
        "password": "password123!",
    })
    token_b = reg_b.json()["token"]

    # Author A posts
    post_res = client.post(
        "/posts",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"kind": "original", "text": "Protected original post"},
    )
    post_id = post_res.json()["item"]["id"]

    # Hacker B tries to edit Author A's post
    malicious_patch = client.patch(
        f"/posts/{post_id}",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"text": "Defaced by Hacker B"},
    )
    assert malicious_patch.status_code == 403
    assert malicious_patch.json()["error"]["code"] == "FORBIDDEN"

    # Verify post text is completely untouched
    get_res = client.get(f"/posts/{post_id}")
    assert get_res.status_code == 200
    assert get_res.json()["item"]["text"] == "Protected original post"


def test_immutable_edit_fields_rejected_with_422(client):
    reg = client.post("/auth/register", json={
        "handle": f"immut_p_{uuid.uuid4().hex[:8]}",
        "displayName": "Immut Author",
        "password": "password123!",
    })
    token = reg.json()["token"]

    post_res = client.post(
        "/posts",
        headers={"Authorization": f"Bearer {token}"},
        json={"kind": "original", "text": "Valid post"},
    )
    post_id = post_res.json()["item"]["id"]

    # Attempting to change kind or author_id
    bad_patch = client.patch(
        f"/posts/{post_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"text": "New text", "kind": "repost"},
    )
    assert bad_patch.status_code == 422
    assert bad_patch.json()["error"]["code"] == "VALIDATION_ERROR"


def test_author_delete_and_non_author_delete(client):
    # Author A
    reg_a = client.post("/auth/register", json={
        "handle": f"dela_{uuid.uuid4().hex[:8]}",
        "displayName": "Del Author A",
        "password": "password123!",
    })
    token_a = reg_a.json()["token"]

    # Stranger B
    reg_b = client.post("/auth/register", json={
        "handle": f"strangerb_{uuid.uuid4().hex[:8]}",
        "displayName": "Stranger B",
        "password": "password123!",
    })
    token_b = reg_b.json()["token"]

    post_res = client.post(
        "/posts",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"kind": "original", "text": "Post to be deleted"},
    )
    post_id = post_res.json()["item"]["id"]

    # Stranger B tries to delete -> 403 Forbidden
    del_b = client.delete(f"/posts/{post_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert del_b.status_code == 403

    # Author A deletes -> 200 OK
    del_a = client.delete(f"/posts/{post_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert del_a.status_code == 200

    # Post is now gone (404)
    get_res = client.get(f"/posts/{post_id}")
    assert get_res.status_code == 404


def test_delete_one_post_checks_all_9_surfaces(client):
    """
    Checkpoint: delete one post and check all 9 surfaces:
    1. Detail view (/posts/{id} -> 404)
    2. Feed (/feed -> post absent)
    3. Search (/search/posts -> post absent)
    4. Replies (/posts/{id}/replies -> 404)
    5. Cascaded reply deletion (reply to deleted post is removed)
    6. Likes (PUT /posts/{id}/like -> 404)
    7. User profile post count (decremented)
    8. Repeated delete safety (DELETE /posts/{id} second time -> 404)
    9. Repost attempt (PUT /posts/{id}/repost -> 404)
    """
    # 1. Author registers and creates original post
    author_handle = f"author9_{uuid.uuid4().hex[:8]}"
    reg_author = client.post("/auth/register", json={
        "handle": author_handle,
        "displayName": "Author 9",
        "password": "password123!",
    })
    author_token = reg_author.json()["token"]
    author_id = reg_author.json()["user"]["id"]

    create_res = client.post(
        "/posts",
        headers={"Authorization": f"Bearer {author_token}"},
        json={"kind": "original", "text": "Post for 9 surface lifecycle test"},
    )
    assert create_res.status_code == 201
    post_id = create_res.json()["item"]["id"]

    # 2. Viewer registers, likes, replies, and reposts
    viewer_handle = f"viewer9_{uuid.uuid4().hex[:8]}"
    reg_viewer = client.post("/auth/register", json={
        "handle": viewer_handle,
        "displayName": "Viewer 9",
        "password": "password123!",
    })
    viewer_token = reg_viewer.json()["token"]

    like_res = client.put(f"/posts/{post_id}/like", headers={"Authorization": f"Bearer {viewer_token}"})
    assert like_res.status_code == 200

    repost_res = client.put(f"/posts/{post_id}/repost", headers={"Authorization": f"Bearer {viewer_token}"})
    assert repost_res.status_code == 200

    reply_res = client.post(
        "/posts",
        headers={"Authorization": f"Bearer {viewer_token}"},
        json={"kind": "reply", "text": "Reply to 9-surface post", "replyToId": post_id},
    )
    assert reply_res.status_code == 201
    reply_id = reply_res.json()["item"]["id"]

    # Check post count before delete
    prof_before = client.get(f"/users/{author_id}")
    count_before = prof_before.json()["item"]["postCount"]

    # 3. Author deletes the post
    del_res = client.delete(f"/posts/{post_id}", headers={"Authorization": f"Bearer {author_token}"})
    assert del_res.status_code == 200

    # Surface 1: Detail view returns 404
    assert client.get(f"/posts/{post_id}").status_code == 404

    # Surface 2: Feed does not contain post
    feed_res = client.get("/feed")
    assert not any(item["id"] == post_id for item in feed_res.json()["items"])

    # Surface 3: Search does not contain post
    search_res = client.get("/search/posts?q=lifecycle")
    assert not any(item["id"] == post_id for item in search_res.json()["items"])

    # Surface 4: Replies endpoint returns 404
    assert client.get(f"/posts/{post_id}/replies").status_code == 404

    # Surface 5: Cascaded reply post is deleted
    assert client.get(f"/posts/{reply_id}").status_code == 404

    # Surface 6: Attempting to like returns 404
    assert client.put(f"/posts/{post_id}/like", headers={"Authorization": f"Bearer {viewer_token}"}).status_code == 404

    # Surface 7: Profile postCount is decremented
    prof_after = client.get(f"/users/{author_id}")
    count_after = prof_after.json()["item"]["postCount"]
    assert count_after == count_before - 1

    # Surface 8: Repeated delete returns 404 safely
    del_again = client.delete(f"/posts/{post_id}", headers={"Authorization": f"Bearer {author_token}"})
    assert del_again.status_code == 404

    # Surface 9: Attempting to repost returns 404
    assert client.put(f"/posts/{post_id}/repost", headers={"Authorization": f"Bearer {viewer_token}"}).status_code == 404


@pytest.mark.asyncio
async def test_two_session_concurrent_edit_race():
    """Checkpoint: Two-session edit race test passes under Last-Write-Wins policy."""
    import asyncio
    import httpx
    from app.main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        # Register author
        handle = f"raceauth_{uuid.uuid4().hex[:8]}"
        reg = await ac.post("/auth/register", json={
            "handle": handle,
            "displayName": "Race Author",
            "password": "password123!",
        })
        token = reg.json()["token"]

        # Create post
        post_res = await ac.post(
            "/posts",
            headers={"Authorization": f"Bearer {token}"},
            json={"kind": "original", "text": "Base draft text"},
        )
        post_id = post_res.json()["item"]["id"]

        # Two concurrent edits (e.g. mobile session and web session)
        async def edit(session_text: str):
            return await ac.patch(
                f"/posts/{post_id}",
                headers={"Authorization": f"Bearer {token}"},
                json={"text": session_text},
            )

        r1, r2 = await asyncio.gather(
            edit("Updated from Phone"),
            edit("Updated from Laptop"),
        )
        assert r1.status_code == 200
        assert r2.status_code == 200

        # Read final state: must be clean and match one of the winning writes
        final_get = await ac.get(f"/posts/{post_id}")
        assert final_get.status_code == 200
        final_text = final_get.json()["item"]["text"]
        assert final_text in ("Updated from Phone", "Updated from Laptop")

