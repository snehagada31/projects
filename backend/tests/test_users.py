from app.fixtures.social_fixtures import USERS


def test_existing_user_profile(client):
    r = client.get(f"/users/{USERS[0]['id']}")
    assert r.status_code == 200
    item = r.json()["item"]
    assert item["handle"] == USERS[0]["handle"]
    assert "postCount" in item
    assert "followerCount" in item
    assert "followingCount" in item


def test_malformed_uuid_returns_400(client):
    r = client.get("/users/garbage")
    assert r.status_code == 400


def test_wellformed_missing_uuid_returns_404(client):
    r = client.get("/users/99999999-9999-4999-8999-999999999999")
    assert r.status_code == 404


def test_user_media(client):
    r = client.get(f"/users/{USERS[0]['id']}/media")
    assert r.status_code == 200
    body = r.json()
    assert "items" in body
    assert "hasMore" in body


def test_list_users(client):
    r = client.get("/users")
    assert r.status_code == 200
    users = r.json()
    assert isinstance(users, list)
    assert len(users) > 0


def test_follow_and_unfollow_user(auth_client):
    target_id = USERS[3]["id"]  # Leo Martins
    r_follow = auth_client.put(f"/users/{target_id}/follow")
    assert r_follow.status_code == 200
    assert r_follow.json()["following"] is True

    r_unfollow = auth_client.delete(f"/users/{target_id}/follow")
    assert r_unfollow.status_code == 200
    assert r_unfollow.json()["following"] is False
