from app.fixtures.social_fixtures import ORIGINALS, REPOSTS


def test_existing_post_detail(client):
    r = client.get(f"/posts/{ORIGINALS[0]['id']}")
    assert r.status_code == 200
    item = r.json()["item"]
    assert item["id"] == ORIGINALS[0]["id"]
    assert item["kind"] == "original"


def test_repost_includes_referenced_post(client):
    r = client.get(f"/posts/{REPOSTS[0]['id']}")
    assert r.status_code == 200
    body = r.json()
    assert body["item"]["kind"] == "repost"
    assert body["referencedPost"] is not None
    assert body["referencedPost"]["id"] == REPOSTS[0]["repost_of_id"]


def test_malformed_uuid_returns_400(client):
    r = client.get("/posts/not-a-uuid")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_wellformed_missing_uuid_returns_404(client):
    r = client.get("/posts/99999999-9999-4999-8999-999999999999")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


def test_post_replies(client):
    r = client.get(f"/posts/{ORIGINALS[0]['id']}/replies")
    assert r.status_code == 200
    body = r.json()
    assert "items" in body
    assert "hasMore" in body


def test_like_and_unlike_post(client):
    post_id = ORIGINALS[0]["id"]
    r_like = client.put(f"/posts/{post_id}/like")
    assert r_like.status_code == 200
    assert r_like.json()["likedByViewer"] is True

    r_unlike = client.delete(f"/posts/{post_id}/like")
    assert r_unlike.status_code == 200
    assert r_unlike.json()["likedByViewer"] is False


def test_search_posts(client):
    r = client.get("/search/posts?q=paginator")
    assert r.status_code == 200
    body = r.json()
    assert "items" in body


def test_create_original_post(client):
    r = client.post("/posts", json={"kind": "original", "text": "A brand new original post from test suite"})
    assert r.status_code == 201
    body = r.json()
    assert "item" in body
    assert body["item"]["text"] == "A brand new original post from test suite"


def test_repost_and_unrepost(client):
    post_id = ORIGINALS[1]["id"]
    r_repost = client.put(f"/posts/{post_id}/repost")
    assert r_repost.status_code == 200
    assert r_repost.json()["repostedByViewer"] is True

    r_unrepost = client.delete(f"/posts/{post_id}/repost")
    assert r_unrepost.status_code == 200
    assert r_unrepost.json()["repostedByViewer"] is False


def test_delete_reply_post(client):
    # Create reply first
    orig_id = ORIGINALS[0]["id"]
    r_create = client.post("/posts", json={"kind": "reply", "text": "Temporary reply to delete", "replyToId": orig_id})
    assert r_create.status_code == 201
    reply_id = r_create.json()["item"]["id"]

    # Delete reply
    r_del = client.delete(f"/posts/{reply_id}")
    assert r_del.status_code == 200
    assert r_del.json()["success"] is True
