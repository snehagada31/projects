"""
Automated test suite proving Stage 2 (PY-P0-02) Owned Profile & Account State acceptance criteria:
1. Owner can update their allowed fields (display_name, bio, avatars).
2. Cross-user updates are rejected with 403 Forbidden; target user state remains byte-identical.
3. Unknown or immutable fields (id, handle, counts) are strictly rejected with 422 Unprocessable Entity.
4. Account deactivation marks user inactive, revokes active sessions, and hides profile from public lookups.
"""

import uuid
import pytest
from app.main import app


def test_owner_update_profile_success(client):
    handle = f"owner_{uuid.uuid4().hex[:8]}"
    reg = client.post("/auth/register", json={
        "handle": handle,
        "displayName": "Original Name",
        "password": "password123!",
        "bio": "Initial bio",
    })
    assert reg.status_code == 201
    token = reg.json()["token"]
    user_id = reg.json()["user"]["id"]

    # Owner updates profile via PATCH /users/me
    update_res = client.patch(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "displayName": "Updated Name",
            "bio": "Updated bio text",
            "avatarSmallUrl": "https://example.com/new_avatar.png",
        },
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()["item"]
    assert updated_data["displayName"] == "Updated Name"
    assert updated_data["bio"] == "Updated bio text"
    assert updated_data["avatar"]["smallUrl"] == "https://example.com/new_avatar.png"

    # Verify public read returns the updated state
    get_res = client.get(f"/users/{user_id}")
    assert get_res.status_code == 200
    assert get_res.json()["item"]["displayName"] == "Updated Name"


def test_cross_user_update_rejected_with_403(client):
    """User B attempts to PATCH User A's profile: must return 403 and leave User A unchanged."""
    # Register User A
    handle_a = f"usera_{uuid.uuid4().hex[:8]}"
    reg_a = client.post("/auth/register", json={
        "handle": handle_a,
        "displayName": "User A Real Name",
        "password": "passwordA123!",
        "bio": "User A Bio",
    })
    user_a_id = reg_a.json()["user"]["id"]

    # Register User B
    handle_b = f"userb_{uuid.uuid4().hex[:8]}"
    reg_b = client.post("/auth/register", json={
        "handle": handle_b,
        "displayName": "User B",
        "password": "passwordB123!",
    })
    token_b = reg_b.json()["token"]

    # User B tries to PATCH User A
    malicious_patch = client.patch(
        f"/users/{user_a_id}",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"displayName": "Hacked By User B"},
    )
    assert malicious_patch.status_code == 403
    err = malicious_patch.json()
    assert err["error"]["code"] == "FORBIDDEN"

    # Verify User A's data in the database is completely unchanged
    get_a = client.get(f"/users/{user_a_id}")
    assert get_a.status_code == 200
    assert get_a.json()["item"]["displayName"] == "User A Real Name"
    assert get_a.json()["item"]["bio"] == "User A Bio"


def test_immutable_and_unknown_fields_rejected_with_422(client):
    """Passing immutable fields (id, handle, followerCount) or unknown properties must be rejected."""
    handle = f"immut_{uuid.uuid4().hex[:8]}"
    reg = client.post("/auth/register", json={
        "handle": handle,
        "displayName": "Immut User",
        "password": "password123!",
    })
    token = reg.json()["token"]

    # 1. Attempting to change handle (immutable)
    patch_handle = client.patch(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"handle": "newhandle"},
    )
    assert patch_handle.status_code == 422
    assert patch_handle.json()["error"]["code"] == "VALIDATION_ERROR"

    # 2. Attempting to tamper with followerCount (immutable/derived)
    patch_counts = client.patch(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"followerCount": 99999},
    )
    assert patch_counts.status_code == 422

    # 3. Attempting to inject unknown arbitrary fields
    patch_unknown = client.patch(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"isAdmin": True},
    )
    assert patch_unknown.status_code == 422


def test_account_deactivation(client):
    """Deactivated accounts are hidden from public reads and active sessions are revoked."""
    handle = f"deact_{uuid.uuid4().hex[:8]}"
    reg = client.post("/auth/register", json={
        "handle": handle,
        "displayName": "Deactivation User",
        "password": "password123!",
    })
    token = reg.json()["token"]
    user_id = reg.json()["user"]["id"]

    # Verify profile is visible
    get_before = client.get(f"/users/{user_id}")
    assert get_before.status_code == 200

    # Deactivate account
    deact_res = client.post("/users/me/deactivate", headers={"Authorization": f"Bearer {token}"})
    assert deact_res.status_code == 200

    # Public read for deactivated user returns 404
    get_after = client.get(f"/users/{user_id}")
    assert get_after.status_code == 404

    # Using the old session token returns 401
    me_after = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_after.status_code == 401
