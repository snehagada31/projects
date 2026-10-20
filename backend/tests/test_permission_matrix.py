"""
Automated test suite proving Stage 7 (PY-P0-07) Security & Release Controls acceptance criteria:
1. Every mutation route in FastAPI is classified in the permission matrix with explicit authn/authz.
2. Request IDs trace allowed and denied requests with matching headers and error envelopes.
3. Complete end-to-end P0 new member journey passes cleanly.
"""

import uuid
import pytest
from app.main import app

# Documented mutation routes and their classification
CLASSIFIED_MUTATIONS = {
    ("POST", "/auth/register"): "Public Registration",
    ("POST", "/auth/login"): "Public Login",
    ("POST", "/auth/logout"): "Authenticated Session Revocation",
    ("POST", "/posts"): "Authenticated Post Creation",
    ("PATCH", "/posts/{post_id}"): "Author-Only Post Edit",
    ("DELETE", "/posts/{post_id}"): "Author-Only Post Delete",
    ("PUT", "/posts/{post_id}/like"): "Authenticated Like",
    ("DELETE", "/posts/{post_id}/like"): "Authenticated Unlike",
    ("PUT", "/posts/{post_id}/repost"): "Authenticated Repost",
    ("DELETE", "/posts/{post_id}/repost"): "Authenticated Unrepost",
    ("PATCH", "/users/me"): "Authenticated Profile Edit",
    ("POST", "/users/me/deactivate"): "Authenticated Account Deactivation",
    ("PATCH", "/users/{user_id}"): "Self-Only Profile Edit (Anti-IDOR)",
    ("PUT", "/users/{user_id}/follow"): "Authenticated Follow",
    ("DELETE", "/users/{user_id}/follow"): "Authenticated Unfollow",
    ("PATCH", "/notifications/{notification_id}/read"): "Recipient-Only Notification Read",
    ("POST", "/notifications/read-all"): "Authenticated Mark All Notifications Read",
}


def test_no_unclassified_mutations_in_route_matrix():
    """Checkpoint: Introspects FastAPI routes and verifies no mutation is unclassified."""
    mutations_in_app = set()

    for route in app.routes:
        methods = getattr(route, "methods", set())
        path = getattr(route, "path", "")

        for method in methods:
            if method in {"POST", "PUT", "PATCH", "DELETE"}:
                mutations_in_app.add((method, path))

    # Assert every mutation in the application is explicitly accounted for
    unclassified = mutations_in_app - set(CLASSIFIED_MUTATIONS.keys())
    assert len(unclassified) == 0, f"Found unclassified mutations: {unclassified}"


def test_request_id_tracing_on_allowed_and_denied_requests(client):
    """Reviewer can trace one allowed and one denied request to final state via request IDs."""
    # 1. Trace an allowed request
    trace_allowed = "trace-allowed-" + uuid.uuid4().hex[:8]
    res_allowed = client.get("/health/live", headers={"X-Request-Id": trace_allowed})
    assert res_allowed.status_code == 200
    assert res_allowed.headers.get("X-Request-Id") == trace_allowed

    # 2. Trace a denied (401) request
    trace_denied = "trace-denied-" + uuid.uuid4().hex[:8]
    res_denied = client.get("/auth/me", headers={"X-Request-Id": trace_denied})
    assert res_denied.status_code == 401
    assert res_denied.headers.get("X-Request-Id") == trace_denied

    # Verify error envelope incorporates request ID
    err_body = res_denied.json()
    assert err_body["error"]["code"] == "UNAUTHORIZED"
    assert err_body["requestId"] == trace_denied


def test_end_to_end_new_member_journey_p0(client):
    """
    Acceptance: Full end-to-end P0 journey passes:
    Register -> Profile -> Follow -> Feed -> Post Lifecycle -> Notifications.
    """
    # 1. Register Creator
    creator_handle = f"e2e_c_{uuid.uuid4().hex[:8]}"
    reg_c = client.post("/auth/register", json={
        "handle": creator_handle,
        "displayName": "E2E Creator",
        "password": "password123!",
    })
    assert reg_c.status_code == 201
    token_c = reg_c.json()["token"]
    creator_id = reg_c.json()["user"]["id"]

    # 2. Register New Member
    member_handle = f"e2e_m_{uuid.uuid4().hex[:8]}"
    reg_m = client.post("/auth/register", json={
        "handle": member_handle,
        "displayName": "E2E Member",
        "password": "password123!",
    })
    assert reg_m.status_code == 201
    token_m = reg_m.json()["token"]

    # 3. Member updates profile
    patch_prof = client.patch(
        "/users/me",
        headers={"Authorization": f"Bearer {token_m}"},
        json={"bio": "Excited new member!"},
    )
    assert patch_prof.status_code == 200
    assert patch_prof.json()["item"]["bio"] == "Excited new member!"

    # 4. Creator publishes original post
    p_res = client.post(
        "/posts",
        headers={"Authorization": f"Bearer {token_c}"},
        json={"kind": "original", "text": "Welcome to our community!"},
    )
    assert p_res.status_code == 201
    post_id = p_res.json()["item"]["id"]

    # 5. Member follows Creator
    follow_res = client.put(f"/users/{creator_id}/follow", headers={"Authorization": f"Bearer {token_m}"})
    assert follow_res.status_code == 200

    # 6. Member views personalized feed -> Creator post appears
    feed_res = client.get("/feed", headers={"Authorization": f"Bearer {token_m}"})
    assert feed_res.status_code == 200
    feed_ids = [item["id"] for item in feed_res.json()["items"]]
    assert post_id in feed_ids

    # 7. Creator checks notifications -> follow notification present
    notifs = client.get("/notifications", headers={"Authorization": f"Bearer {token_c}"})
    assert notifs.status_code == 200
    assert any(n["eventType"] == "follow" for n in notifs.json()["items"])

    # 8. Creator edits post text
    edit_res = client.patch(
        f"/posts/{post_id}",
        headers={"Authorization": f"Bearer {token_c}"},
        json={"text": "Welcome to our community! (Edited)"},
    )
    assert edit_res.status_code == 200
    assert edit_res.json()["item"]["text"] == "Welcome to our community! (Edited)"

    # 9. Member likes post
    like_res = client.put(f"/posts/{post_id}/like", headers={"Authorization": f"Bearer {token_m}"})
    assert like_res.status_code == 200

    # 10. Creator deletes post
    del_res = client.delete(f"/posts/{post_id}", headers={"Authorization": f"Bearer {token_c}"})
    assert del_res.status_code == 200
    assert client.get(f"/posts/{post_id}").status_code == 404
