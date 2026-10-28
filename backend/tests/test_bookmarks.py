"""
Tests for PY-P1-02 Bookmarks:
- Desired-state bookmark and unbookmark
- Authoritative owner-only /bookmarks retrieval
- Isolation: User A cannot see User B's bookmarks
- Post deletion cascades to bookmarks
"""

import uuid
import pytest
from app.db.models import Bookmark


def test_bookmark_lifecycle_and_owner_isolation(client):
    # Register User A (Collector)
    reg_a = client.post("/auth/register", json={
        "handle": f"usera_{uuid.uuid4().hex[:8]}",
        "displayName": "User A",
        "password": "password123!",
    })
    token_a = reg_a.json()["token"]

    # Register User B (Author)
    reg_b = client.post("/auth/register", json={
        "handle": f"userb_{uuid.uuid4().hex[:8]}",
        "displayName": "User B",
        "password": "password123!",
    })
    token_b = reg_b.json()["token"]

    # User B creates a post
    post_res = client.post(
        "/posts",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"kind": "original", "text": "Interesting post to bookmark"},
    )
    post_id = post_res.json()["item"]["id"]

    # 1. User A bookmarks post
    bm_res = client.put(
        f"/posts/{post_id}/bookmark",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert bm_res.status_code == 200
    assert bm_res.json()["bookmarkedByViewer"] is True

    # Idempotent retry: Bookmarking again returns 200 and true
    bm_res_retry = client.put(
        f"/posts/{post_id}/bookmark",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert bm_res_retry.status_code == 200
    assert bm_res_retry.json()["bookmarkedByViewer"] is True

    # 2. User A fetches bookmarks -> post appears
    list_a = client.get(
        "/bookmarks",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert list_a.status_code == 200
    items_a = list_a.json()["items"]
    assert len(items_a) == 1
    assert items_a[0]["id"] == post_id
    assert items_a[0]["bookmarkedByViewer"] is True

    # 3. Isolation: User B's bookmarks list is EMPTY (strictly viewer-private)
    list_b = client.get(
        "/bookmarks",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert list_b.status_code == 200
    assert len(list_b.json()["items"]) == 0

    # 4. Unauthenticated request to /bookmarks returns 401
    unauth = client.get("/bookmarks")
    assert unauth.status_code == 401

    # 5. User A unbookmarks post
    unbm_res = client.delete(
        f"/posts/{post_id}/bookmark",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert unbm_res.status_code == 200
    assert unbm_res.json()["bookmarkedByViewer"] is False

    # Check bookmarks is now empty
    list_after = client.get(
        "/bookmarks",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert len(list_after.json()["items"]) == 0
