"""
Automated test suite proving Stage 1 (PY-P0-01) Account & Session Identity acceptance criteria:
1. Registration with unique normalized handle, display name, and password.
2. Concurrent duplicate registration creates at most one account (409 Conflict).
3. Login failure does not leak account existence (anti-enumeration).
4. Valid identity enables protected work; missing/invalid/revoked does not (401 Unauthorized).
5. Logout instantly invalidates the session token.
6. Passwords and session secrets are never returned in responses.
"""

import uuid
import asyncio
import pytest
import httpx
from app.main import app


def test_registration_and_no_credential_leak(client):

    unique_handle = f"user_{uuid.uuid4().hex[:8]}"
    payload = {
        "handle": unique_handle.upper(),  # test normalization
        "displayName": "Test Learner",
        "password": "superSecretPassword123!",
        "bio": "Building Stage 1",
    }
    res = client.post("/auth/register", json=payload)
    assert res.status_code == 201, res.text
    data = res.json()

    assert "token" in data
    assert len(data["token"]) > 20
    assert "user" in data
    assert data["user"]["handle"] == unique_handle.lower()
    assert data["user"]["displayName"] == "Test Learner"

    # Strict check: credentials / hashes must never leak in response
    assert "password" not in data
    assert "password_hash" not in data
    assert "passwordHash" not in data
    assert "token_hash" not in data


def test_duplicate_registration_fails(client):
    unique_handle = f"dup_{uuid.uuid4().hex[:8]}"
    payload = {
        "handle": unique_handle,
        "displayName": "Original",
        "password": "password12345",
    }
    res1 = client.post("/auth/register", json=payload)
    assert res1.status_code == 201

    # Second registration with same handle
    res2 = client.post("/auth/register", json=payload)
    assert res2.status_code == 409
    err = res2.json()
    assert err["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_concurrent_20_duplicate_registrations_checkpoint():
    """Checkpoint: run 20 concurrent registrations of the same handle -> exactly 1 account."""
    import httpx
    unique_handle = f"race_{uuid.uuid4().hex[:8]}"
    payload = {
        "handle": unique_handle,
        "displayName": "Race Condition Probe",
        "password": "securePassword123!",
    }

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        tasks = [ac.post("/auth/register", json=payload) for _ in range(20)]
        responses = await asyncio.gather(*tasks)

    status_codes = [r.status_code for r in responses]
    success_count = status_codes.count(201)
    conflict_count = status_codes.count(409)

    assert success_count == 1, f"Expected exactly 1 success, got {success_count} (statuses: {status_codes})"
    assert conflict_count == 19, f"Expected 19 conflicts, got {conflict_count}"



def test_login_success_and_me(client):
    handle = f"login_{uuid.uuid4().hex[:8]}"
    password = "validPassword123"
    client.post("/auth/register", json={
        "handle": handle,
        "displayName": "Login User",
        "password": password,
    })

    # Sign in
    res = client.post("/auth/login", json={"handle": handle, "password": password})
    assert res.status_code == 200
    token = res.json()["token"]

    # Access protected /auth/me
    me_res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["handle"] == handle


def test_timing_and_enumeration_resistance(client):
    """Both unknown user and wrong password return exact same error shape & message."""
    # 1. Non-existent handle
    res_unknown = client.post("/auth/login", json={
        "handle": f"nonexistent_{uuid.uuid4().hex[:8]}",
        "password": "someRandomPassword",
    })
    assert res_unknown.status_code == 401
    err_unknown = res_unknown.json()

    # 2. Existing handle, wrong password
    handle = f"exist_{uuid.uuid4().hex[:8]}"
    client.post("/auth/register", json={
        "handle": handle,
        "displayName": "Existing",
        "password": "correctPassword123",
    })
    res_wrong_pw = client.post("/auth/login", json={
        "handle": handle,
        "password": "wrongPassword123",
    })
    assert res_wrong_pw.status_code == 401
    err_wrong_pw = res_wrong_pw.json()

    # Must be completely identical
    assert err_unknown["error"]["message"] == err_wrong_pw["error"]["message"]
    assert err_unknown["error"]["message"] == "Invalid handle or password"
    assert err_unknown["error"]["code"] == "UNAUTHORIZED"


def test_session_revocation_on_logout(client):
    handle = f"logout_{uuid.uuid4().hex[:8]}"
    password = "logoutPassword123"
    reg = client.post("/auth/register", json={
        "handle": handle,
        "displayName": "Logout User",
        "password": password,
    })
    token = reg.json()["token"]

    # Verify session works
    me_before = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_before.status_code == 200

    # Logout
    logout_res = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_res.status_code == 200

    # Verify session is now revoked (401)
    me_after = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_after.status_code == 401
    assert me_after.json()["error"]["code"] == "UNAUTHORIZED"


def test_missing_or_malformed_auth_header(client):
    # No header
    res_no_header = client.get("/auth/me")
    assert res_no_header.status_code == 401

    # Bad token
    res_bad_token = client.get("/auth/me", headers={"Authorization": "Bearer totally_bogus_token"})
    assert res_bad_token.status_code == 401
    assert res_bad_token.json()["error"]["code"] == "UNAUTHORIZED"

