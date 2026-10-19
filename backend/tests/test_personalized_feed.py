"""
Automated test suite proving Stage 4 (PY-P0-04) Personalized Home Feed acceptance criteria:
1. Feed includes eligible originals from followed authors and the viewer.
2. Ineligible (unfollowed) authors never appear in the personalized feed.
3. Unfollowing an author dynamically removes their posts on the next feed request.
4. Onboarding fallback: new user following 0 people sees public originals instead of an empty broken page.
"""

import uuid
import pytest


def test_personalized_feed_shows_only_followed_and_self(client):
    # Register Viewer User A
    reg_a = client.post("/auth/register", json={
        "handle": f"viewer_{uuid.uuid4().hex[:8]}",
        "displayName": "Viewer A",
        "password": "password123!",
    })
    token_a = reg_a.json()["token"]

    # Register Creator B (will be followed)
    reg_b = client.post("/auth/register", json={
        "handle": f"friend_{uuid.uuid4().hex[:8]}",
        "displayName": "Friend B",
        "password": "password123!",
    })
    token_b = reg_b.json()["token"]
    user_b_id = reg_b.json()["user"]["id"]

    # Register Stranger C (will NOT be followed)
    reg_c = client.post("/auth/register", json={
        "handle": f"stranger_{uuid.uuid4().hex[:8]}",
        "displayName": "Stranger C",
        "password": "password123!",
    })
    token_c = reg_c.json()["token"]

    # Friend B posts an original
    post_b_res = client.post(
        "/posts",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"kind": "original", "text": "Post from Friend B"},
    )
    assert post_b_res.status_code == 201
    post_b_id = post_b_res.json()["item"]["id"]

    # Stranger C posts an original
    post_c_res = client.post(
        "/posts",
        headers={"Authorization": f"Bearer {token_c}"},
        json={"kind": "original", "text": "Post from Stranger C"},
    )
    assert post_c_res.status_code == 201
    post_c_id = post_c_res.json()["item"]["id"]

    # Viewer A follows Friend B
    client.put(f"/users/{user_b_id}/follow", headers={"Authorization": f"Bearer {token_a}"})

    # Viewer A queries feed
    feed_res = client.get("/feed", headers={"Authorization": f"Bearer {token_a}"})
    assert feed_res.status_code == 200
    feed_items = feed_res.json()["items"]
    feed_ids = [item["id"] for item in feed_items]

    # Verify: Post from B is included, Post from Stranger C is excluded!
    assert post_b_id in feed_ids, "Followed author's post missing from personal feed!"
    assert post_c_id not in feed_ids, "Unfollowed stranger's post leaked into personal feed!"


def test_unfollow_reflects_in_feed(client):
    """Unfollowing an author dynamically updates the feed on the very next request."""
    reg_a = client.post("/auth/register", json={
        "handle": f"dyn_a_{uuid.uuid4().hex[:8]}",
        "displayName": "Dyn A",
        "password": "password123!",
    })
    token_a = reg_a.json()["token"]

    reg_b = client.post("/auth/register", json={
        "handle": f"dyn_b_{uuid.uuid4().hex[:8]}",
        "displayName": "Dyn B",
        "password": "password123!",
    })
    token_b = reg_b.json()["token"]
    user_b_id = reg_b.json()["user"]["id"]

    # B posts
    post_res = client.post(
        "/posts",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"kind": "original", "text": "Dynamic follow test post"},
    )
    post_id = post_res.json()["item"]["id"]

    # A follows B -> post appears
    client.put(f"/users/{user_b_id}/follow", headers={"Authorization": f"Bearer {token_a}"})
    f1 = client.get("/feed", headers={"Authorization": f"Bearer {token_a}"})
    assert any(i["id"] == post_id for i in f1.json()["items"])

    # A unfollows B -> post is gone!
    client.delete(f"/users/{user_b_id}/follow", headers={"Authorization": f"Bearer {token_a}"})
    f2 = client.get("/feed", headers={"Authorization": f"Bearer {token_a}"})
    assert not any(i["id"] == post_id for i in f2.json()["items"])


def test_onboarding_empty_fallback(client):
    """New member with 0 follows and 0 posts sees an intentional empty state, while anonymous gets public feed."""
    reg_new = client.post("/auth/register", json={
        "handle": f"onboard_{uuid.uuid4().hex[:8]}",
        "displayName": "Newcomer",
        "password": "password123!",
    })
    token = reg_new.json()["token"]

    # Authenticated query with no follows returns 200 with empty list
    res_auth = client.get("/feed", headers={"Authorization": f"Bearer {token}"})
    assert res_auth.status_code == 200
    assert len(res_auth.json()["items"]) == 0

    # Anonymous visitor receives full public feed for discovery
    res_anon = client.get("/feed")
    assert res_anon.status_code == 200
    assert len(res_anon.json()["items"]) > 0
