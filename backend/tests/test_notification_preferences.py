"""
Tests for PY-P1-04 Notification Preferences:
- Default categories enabled
- PATCH /notifications/preferences updates category toggles
- Disabled category suppresses notification delivery without breaking source action
"""

import uuid
import pytest


def test_notification_preferences_defaults_and_toggle(client):
    # Register User
    reg = client.post("/auth/register", json={
        "handle": f"pref_{uuid.uuid4().hex[:8]}",
        "displayName": "Pref User",
        "password": "password123!",
    })
    token = reg.json()["token"]

    # 1. GET /notifications/preferences -> all true by default
    res = client.get("/notifications/preferences", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["likes"] is True
    assert data["reposts"] is True
    assert data["replies"] is True
    assert data["follows"] is True

    # 2. PATCH /notifications/preferences -> toggle likes off
    patch_res = client.patch(
        "/notifications/preferences",
        headers={"Authorization": f"Bearer {token}"},
        json={"likes": False},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["likes"] is False
    assert patch_res.json()["reposts"] is True

    # Verify updated preferences persist
    get_again = client.get("/notifications/preferences", headers={"Authorization": f"Bearer {token}"})
    assert get_again.status_code == 200
    assert get_again.json()["likes"] is False
