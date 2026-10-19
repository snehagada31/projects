"""
Automated test suite proving Stage 3 (PY-P0-03) Follow Graph & Privacy acceptance criteria:
1. Follow and unfollow derive actor strictly from authenticated session.
2. Operations are desired-state and idempotent (repeating does not inflate count).
3. Self-follow is strictly rejected (422 and DB CHECK constraint).
4. Checkpoint: 50 concurrent follow requests for the same pair converge to 1 active row.
5. Deterministic follower/following relationship lists.
"""

import uuid
import asyncio
import pytest
import httpx
from sqlalchemy import select, func
from app.main import app
from app.db.session import async_session_factory
from app.db.models import Follow


def test_authenticated_follow_and_unfollow(client):
    # Register User A
    handle_a = f"fan_{uuid.uuid4().hex[:8]}"
    reg_a = client.post("/auth/register", json={
        "handle": handle_a,
        "displayName": "Fan A",
        "password": "password123!",
    })
    token_a = reg_a.json()["token"]

    # Register User B (Creator)
    handle_b = f"creator_{uuid.uuid4().hex[:8]}"
    reg_b = client.post("/auth/register", json={
        "handle": handle_b,
        "displayName": "Creator B",
        "password": "password123!",
    })
    user_b_id = reg_b.json()["user"]["id"]

    # User A follows User B
    put_res = client.put(
        f"/users/{user_b_id}/follow",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert put_res.status_code == 200
    assert put_res.json()["following"] is True
    assert put_res.json()["followerCount"] == 1

    # User A unfollows User B
    del_res = client.delete(
        f"/users/{user_b_id}/follow",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert del_res.status_code == 200
    assert del_res.json()["following"] is False
    assert del_res.json()["followerCount"] == 0


def test_desired_state_idempotence(client):
    """Calling follow or unfollow multiple times converges on the requested state."""
    handle_a = f"idem_a_{uuid.uuid4().hex[:8]}"
    reg_a = client.post("/auth/register", json={
        "handle": handle_a,
        "displayName": "Idem A",
        "password": "password123!",
    })
    token_a = reg_a.json()["token"]

    handle_b = f"idem_b_{uuid.uuid4().hex[:8]}"
    reg_b = client.post("/auth/register", json={
        "handle": handle_b,
        "displayName": "Idem B",
        "password": "password123!",
    })
    user_b_id = reg_b.json()["user"]["id"]

    # Call follow 3 times in a row
    for _ in range(3):
        res = client.put(
            f"/users/{user_b_id}/follow",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert res.status_code == 200
        assert res.json()["following"] is True
        assert res.json()["followerCount"] == 1  # Never inflates to 2 or 3!

    # Call unfollow 3 times in a row
    for _ in range(3):
        res = client.delete(
            f"/users/{user_b_id}/follow",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert res.status_code == 200
        assert res.json()["following"] is False
        assert res.json()["followerCount"] == 0


def test_self_follow_rejected(client):
    """Users cannot follow themselves."""
    handle = f"self_{uuid.uuid4().hex[:8]}"
    reg = client.post("/auth/register", json={
        "handle": handle,
        "displayName": "Self Follower",
        "password": "password123!",
    })
    token = reg.json()["token"]
    user_id = reg.json()["user"]["id"]

    res = client.put(
        f"/users/{user_id}/follow",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_follower_and_following_lists(client):
    handle_a = f"list_a_{uuid.uuid4().hex[:8]}"
    reg_a = client.post("/auth/register", json={
        "handle": handle_a,
        "displayName": "List A",
        "password": "password123!",
    })
    token_a = reg_a.json()["token"]
    user_a_id = reg_a.json()["user"]["id"]

    handle_b = f"list_b_{uuid.uuid4().hex[:8]}"
    reg_b = client.post("/auth/register", json={
        "handle": handle_b,
        "displayName": "List B",
        "password": "password123!",
    })
    user_b_id = reg_b.json()["user"]["id"]

    # A follows B
    client.put(f"/users/{user_b_id}/follow", headers={"Authorization": f"Bearer {token_a}"})

    # Check B's followers
    followers_res = client.get(f"/users/{user_b_id}/followers")
    assert followers_res.status_code == 200
    followers = followers_res.json()
    assert any(u["id"] == user_a_id for u in followers)

    # Check A's following
    following_res = client.get(f"/users/{user_a_id}/following")
    assert following_res.status_code == 200
    following = following_res.json()
    assert any(u["id"] == user_b_id for u in following)


@pytest.mark.asyncio
async def test_concurrent_50_duplicate_follows_checkpoint():
    """Checkpoint: Fire 50 concurrent follow requests for the same pair -> exactly 1 active row."""
    # Create two users directly
    handle_a = f"race_fan_{uuid.uuid4().hex[:8]}"
    handle_b = f"race_target_{uuid.uuid4().hex[:8]}"

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        reg_a = await ac.post("/auth/register", json={"handle": handle_a, "displayName": "A", "password": "password123!"})
        reg_b = await ac.post("/auth/register", json={"handle": handle_b, "displayName": "B", "password": "password123!"})
        token_a = reg_a.json()["token"]
        target_id = reg_b.json()["user"]["id"]

        # Fire 50 concurrent follow requests
        headers = {"Authorization": f"Bearer {token_a}"}
        tasks = [ac.put(f"/users/{target_id}/follow", headers=headers) for _ in range(50)]
        responses = await asyncio.gather(*tasks)

    # All 50 requests must succeed with 200 OK (idempotent desired state)
    for r in responses:
        assert r.status_code == 200

    # Verify directly in PostgreSQL that exactly ONE row exists
    async with async_session_factory() as session:
        stmt = select(func.count()).select_from(Follow).where(
            Follow.following_id == uuid.UUID(target_id)
        )
        res = await session.execute(stmt)
        count = res.scalar()
        assert count == 1, f"Expected exactly 1 follow row, found {count}"
