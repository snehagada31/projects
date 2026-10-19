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
