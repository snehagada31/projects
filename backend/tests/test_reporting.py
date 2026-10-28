"""
Tests for PY-P1-06: Reporting & Moderation.
- Controlled reasons validation (spam, harassment, hate_speech, misinformation)
- Duplicate prevention (re-reporting returns existing audit state)
- Non-existent post error
- Unauthorized rejection
"""

import uuid
from app.fixtures.social_fixtures import ALL_POSTS

ORIGINAL_POST_ID = ALL_POSTS[0]["id"]


def test_report_post_requires_auth(client):
    res = client.post(f"/posts/{ORIGINAL_POST_ID}/report", json={"reason": "spam"})
    assert res.status_code == 401


def test_report_post_controlled_reasons(auth_client):
    # Valid controlled reasons
    for reason in ["spam", "harassment", "hate_speech", "misinformation"]:
        res = auth_client.post(
            f"/posts/{ORIGINAL_POST_ID}/report",
            json={"reason": reason, "notes": f"Testing reason {reason}"}
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["status"] == "pending"
        assert "reportId" in body


def test_report_post_invalid_reason_rejected(auth_client):
    res = auth_client.post(
        f"/posts/{ORIGINAL_POST_ID}/report",
        json={"reason": "i_dont_like_this", "notes": "Invalid reason"}
    )
    assert res.status_code == 422


def test_report_post_duplicate_is_idempotent(auth_client):
    res1 = auth_client.post(
        f"/posts/{ORIGINAL_POST_ID}/report",
        json={"reason": "spam", "notes": "First report"}
    )
    assert res1.status_code == 200
    report_id1 = res1.json()["reportId"]

    # Second report by same actor on same post
    res2 = auth_client.post(
        f"/posts/{ORIGINAL_POST_ID}/report",
        json={"reason": "spam", "notes": "Duplicate report"}
    )
    assert res2.status_code == 200
    report_id2 = res2.json()["reportId"]
    assert report_id1 == report_id2


def test_report_nonexistent_post(auth_client):
    missing_id = str(uuid.uuid4())
    res = auth_client.post(f"/posts/{missing_id}/report", json={"reason": "spam"})
    assert res.status_code == 404
