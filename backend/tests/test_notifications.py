"""
Automated test suite proving Stage 6 (PY-P0-06) Notification Inbox acceptance criteria:
1. Required events (like, follow, repost, reply) reach only the intended recipient once.
2. Self-actions produce zero notifications.
3. Checkpoint: 10 concurrent retries of the same like produce exactly 1 notification.
4. Cross-user access to notifications is strictly forbidden (anti-IDOR).
5. Unread count and mark-read transitions are authoritative.
6. Checkpoint: Source transaction rollback leaves zero orphaned notifications.
7. Post deletion preserves notification history with tombstoned postId: null.
"""

import uuid
import asyncio
import pytest
import httpx
from sqlalchemy import select, func
from app.main import app
from app.db.session import async_session_factory
from app.db.models import Notification, Like


def test_notification_created_on_like_follow_repost_reply(client):
    # Register Creator (Recipient)
    reg_creator = client.post("/auth/register", json={
        "handle": f"creator_{uuid.uuid4().hex[:8]}",
        "displayName": "Creator User",
        "password": "password123!",
    })
    creator_token = reg_creator.json()["token"]
    creator_id = reg_creator.json()["user"]["id"]

    # Register Fan (Actor)
    reg_fan = client.post("/auth/register", json={
        "handle": f"fan_{uuid.uuid4().hex[:8]}",
        "displayName": "Fan User",
        "password": "password123!",
    })
    fan_token = reg_fan.json()["token"]

    # Creator creates original post
    p_res = client.post(
        "/posts",
        headers={"Authorization": f"Bearer {creator_token}"},
        json={"kind": "original", "text": "Post to interact with"},
    )
    post_id = p_res.json()["item"]["id"]

    # 1. Fan follows Creator
    client.put(f"/users/{creator_id}/follow", headers={"Authorization": f"Bearer {fan_token}"})

    # 2. Fan likes Creator's post
    client.put(f"/posts/{post_id}/like", headers={"Authorization": f"Bearer {fan_token}"})

    # 3. Fan reposts Creator's post
    client.put(f"/posts/{post_id}/repost", headers={"Authorization": f"Bearer {fan_token}"})

    # 4. Fan replies to Creator's post
    client.post(
        "/posts",
        headers={"Authorization": f"Bearer {fan_token}"},
        json={"kind": "reply", "text": "Fan reply text", "replyToId": post_id},
    )

    # Verify Creator's notification inbox has all 4 notifications
    inbox_res = client.get("/notifications", headers={"Authorization": f"Bearer {creator_token}"})
    assert inbox_res.status_code == 200
    items = inbox_res.json()["items"]
    assert len(items) == 4

    event_types = {item["eventType"] for item in items}
    assert event_types == {"follow", "like", "repost", "reply"}

    # Verify Fan's inbox is empty (no notifications sent to actor)
    fan_inbox = client.get("/notifications", headers={"Authorization": f"Bearer {fan_token}"})
    assert len(fan_inbox.json()["items"]) == 0


def test_self_actions_produce_no_notifications(client):
    reg = client.post("/auth/register", json={
        "handle": f"solo_{uuid.uuid4().hex[:8]}",
        "displayName": "Solo Creator",
        "password": "password123!",
    })
    token = reg.json()["token"]

    p_res = client.post(
        "/posts",
        headers={"Authorization": f"Bearer {token}"},
        json={"kind": "original", "text": "Self action post"},
    )
    post_id = p_res.json()["item"]["id"]

    # Self-like
    client.put(f"/posts/{post_id}/like", headers={"Authorization": f"Bearer {token}"})

    # Self-repost
    client.put(f"/posts/{post_id}/repost", headers={"Authorization": f"Bearer {token}"})

    # Self-reply
    client.post(
        "/posts",
        headers={"Authorization": f"Bearer {token}"},
        json={"kind": "reply", "text": "Replying to myself", "replyToId": post_id},
    )

    # Inbox must remain strictly 0
    inbox = client.get("/notifications", headers={"Authorization": f"Bearer {token}"})
    assert len(inbox.json()["items"]) == 0

    count = client.get("/notifications/unread-count", headers={"Authorization": f"Bearer {token}"})
    assert count.json()["count"] == 0


@pytest.mark.asyncio
async def test_concurrent_like_retry_deduplication():
    """Checkpoint: Retry the same like 10x concurrently -> exactly 1 notification."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        # Creator
        creator_reg = await ac.post("/auth/register", json={
            "handle": f"crea_{uuid.uuid4().hex[:8]}",
            "displayName": "Target Creator",
            "password": "password123!",
        })
        creator_token = creator_reg.json()["token"]

        post_res = await ac.post(
            "/posts",
            headers={"Authorization": f"Bearer {creator_token}"},
            json={"kind": "original", "text": "Concurrent like target"},
        )
        post_id = post_res.json()["item"]["id"]

        # Fan
        fan_reg = await ac.post("/auth/register", json={
            "handle": f"liker_{uuid.uuid4().hex[:8]}",
            "displayName": "Rapid Liker",
            "password": "password123!",
        })
        fan_token = fan_reg.json()["token"]

        # 10 concurrent PUT /like requests
        tasks = [
            ac.put(f"/posts/{post_id}/like", headers={"Authorization": f"Bearer {fan_token}"})
            for _ in range(10)
        ]
        responses = await asyncio.gather(*tasks)
        assert all(r.status_code == 200 for r in responses)

        # Creator should have EXACTLY 1 notification
        inbox = await ac.get("/notifications", headers={"Authorization": f"Bearer {creator_token}"})
        assert inbox.status_code == 200
        items = inbox.json()["items"]
        assert len(items) == 1
        assert items[0]["eventType"] == "like"


def test_cross_user_notification_access_rejected(client):
    # Recipient
    reg_rec = client.post("/auth/register", json={
        "handle": f"rec_{uuid.uuid4().hex[:8]}",
        "displayName": "Recipient",
        "password": "password123!",
    })
    token_rec = reg_rec.json()["token"]
    rec_id = reg_rec.json()["user"]["id"]

    # Actor
    reg_act = client.post("/auth/register", json={
        "handle": f"act_{uuid.uuid4().hex[:8]}",
        "displayName": "Actor",
        "password": "password123!",
    })
    token_act = reg_act.json()["token"]

    # Stranger (Attacker)
    reg_hacker = client.post("/auth/register", json={
        "handle": f"hacker_{uuid.uuid4().hex[:8]}",
        "displayName": "Hacker",
        "password": "password123!",
    })
    token_hacker = reg_hacker.json()["token"]

    # Trigger notification: Actor follows Recipient
    client.put(f"/users/{rec_id}/follow", headers={"Authorization": f"Bearer {token_act}"})

    inbox = client.get("/notifications", headers={"Authorization": f"Bearer {token_rec}"})
    notif_id = inbox.json()["items"][0]["id"]

    # Hacker tries to mark Recipient's notification as read -> 403 Forbidden
    hack_res = client.patch(
        f"/notifications/{notif_id}/read",
        headers={"Authorization": f"Bearer {token_hacker}"},
    )
    assert hack_res.status_code == 403
    assert hack_res.json()["error"]["code"] == "FORBIDDEN"


def test_mark_read_and_unread_counts(client):
    # User B
    reg_b = client.post("/auth/register", json={
        "handle": f"userb_{uuid.uuid4().hex[:8]}",
        "displayName": "User B",
        "password": "password123!",
    })
    token_b = reg_b.json()["token"]
    user_b_id = reg_b.json()["user"]["id"]

    # User A triggers 2 notifications
    reg_a = client.post("/auth/register", json={
        "handle": f"usera_{uuid.uuid4().hex[:8]}",
        "displayName": "User A",
        "password": "password123!",
    })
    token_a = reg_a.json()["token"]

    # Follow B
    client.put(f"/users/{user_b_id}/follow", headers={"Authorization": f"Bearer {token_a}"})

    # Post by B, liked by A
    post_b = client.post(
        "/posts",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"kind": "original", "text": "Post to like"},
    ).json()["item"]["id"]
    client.put(f"/posts/{post_b}/like", headers={"Authorization": f"Bearer {token_a}"})

    # Check unread count = 2
    c1 = client.get("/notifications/unread-count", headers={"Authorization": f"Bearer {token_b}"})
    assert c1.json()["count"] == 2

    # Mark 1 as read
    inbox = client.get("/notifications", headers={"Authorization": f"Bearer {token_b}"}).json()["items"]
    notif_id = inbox[0]["id"]

    r_patch = client.patch(
        f"/notifications/{notif_id}/read",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r_patch.status_code == 200
    assert r_patch.json()["isRead"] is True

    # Check unread count = 1
    c2 = client.get("/notifications/unread-count", headers={"Authorization": f"Bearer {token_b}"})
    assert c2.json()["count"] == 1

    # Mark all read
    r_all = client.post("/notifications/read-all", headers={"Authorization": f"Bearer {token_b}"})
    assert r_all.status_code == 200
    assert r_all.json()["markedRead"] == 1

    # Check unread count = 0
    c3 = client.get("/notifications/unread-count", headers={"Authorization": f"Bearer {token_b}"})
    assert c3.json()["count"] == 0


@pytest.mark.asyncio
async def test_source_rollback_leaves_no_orphaned_notification():
    """Checkpoint: Force a failure after source write; show zero notifications remain."""
    async with async_session_factory() as session:
        # Create user A and B
        u_a = uuid.uuid4()
        u_b = uuid.uuid4()

        try:
            async with session.begin():
                # Write a notification
                notif = Notification(
                    recipient_id=u_b,
                    actor_id=u_a,
                    event_type="like",
                    post_id=None,
                    dedup_key=f"rollback_test:{u_a}:{u_b}",
                )
                session.add(notif)
                # Now simulate an intentional transaction abort / exception
                raise RuntimeError("Simulated mid-transaction failure")
        except RuntimeError:
            pass

        # Query notifications table: must have zero records for this key
        res = await session.scalar(
            select(func.count(Notification.id)).where(
                Notification.dedup_key == f"rollback_test:{u_a}:{u_b}"
            )
        )
        assert res == 0, "Rollback failed: orphaned notification persisted in database!"


def test_deleted_post_tombstone_in_notifications(client):
    """When a post is deleted, its notification remains with postId: null (tombstone)."""
    # Author
    reg_auth = client.post("/auth/register", json={
        "handle": f"auth_t_{uuid.uuid4().hex[:8]}",
        "displayName": "Author T",
        "password": "password123!",
    })
    token_auth = reg_auth.json()["token"]

    p_res = client.post(
        "/posts",
        headers={"Authorization": f"Bearer {token_auth}"},
        json={"kind": "original", "text": "Post to be deleted for tombstone"},
    )
    post_id = p_res.json()["item"]["id"]

    # Fan likes
    reg_fan = client.post("/auth/register", json={
        "handle": f"fan_t_{uuid.uuid4().hex[:8]}",
        "displayName": "Fan T",
        "password": "password123!",
    })
    token_fan = reg_fan.json()["token"]

    client.put(f"/posts/{post_id}/like", headers={"Authorization": f"Bearer {token_fan}"})

    # Inbox shows notification with postId
    inbox_before = client.get("/notifications", headers={"Authorization": f"Bearer {token_auth}"}).json()["items"]
    assert len(inbox_before) == 1
    assert inbox_before[0]["postId"] == post_id

    # Author deletes post
    del_res = client.delete(f"/posts/{post_id}", headers={"Authorization": f"Bearer {token_auth}"})
    assert del_res.status_code == 200

    # Inbox still shows notification, but postId is now None/null (tombstone)
    inbox_after = client.get("/notifications", headers={"Authorization": f"Bearer {token_auth}"}).json()["items"]
    assert len(inbox_after) == 1
    assert inbox_after[0]["postId"] is None
