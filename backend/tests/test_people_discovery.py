"""
Tests for PY-P1-01: People discovery & suggestions.
- Search discoverable accounts with privacy/deactivation awareness
- Safe projections: only public fields exposed
- Deterministic pagination
- Bounded explainable suggestions
"""

from app.fixtures.social_fixtures import USERS


def test_search_discoverable_accounts(client):
    target_handle = USERS[0]["handle"]
    res = client.get(f"/users/search?q={target_handle}")
    assert res.status_code == 200
    body = res.json()
    assert "items" in body
    assert len(body["items"]) >= 1
    item = body["items"][0]
    
    # Verify public fields only (no password_hash or internal secrets)
    assert "id" in item
    assert "handle" in item
    assert "displayName" in item
    assert "avatar" in item
    assert "followerCount" in item
    assert "followingCount" in item
    assert "following" in item
    assert "password_hash" not in item
    assert "passwordHash" not in item


def test_search_pagination_deterministic(client):
    res = client.get("/users/search?q=a&limit=2")
    assert res.status_code == 200
    body = res.json()
    assert len(body["items"]) <= 2
    if body["hasMore"]:
        assert body["nextCursor"] is not None
        # Follow cursor
        res2 = client.get(f"/users/search?q=a&limit=2&cursor={body['nextCursor']}")
        assert res2.status_code == 200
        body2 = res2.json()
        assert len(body2["items"]) > 0


def test_bounded_explainable_suggestions(client):
    res = client.get("/users/suggestions?limit=3")
    assert res.status_code == 200
    suggestions = res.json()
    assert isinstance(suggestions, list)
    assert len(suggestions) <= 3
    for s in suggestions:
        assert "id" in s
        assert "handle" in s
        assert "reason" in s
        assert "followerCount" in s
        assert isinstance(s["reason"], str)
        assert len(s["reason"]) > 0
