"""
Proves the repository pattern actually does what it's for: a test can
swap the real fixture data for completely fake, controlled data, WITHOUT
touching any route code. This is the exact acceptance evidence PY-S03
asks for.
"""

from app.main import app
from app.api.feed import get_social_repository


class FakeRepository:
    """Deliberately returns totally different data than the real
    fixtures — if this test passes, the route is genuinely using
    WHATEVER repository is injected, not hardcoded to the real one."""

    def get_originals_sorted(self):
        return [{
            "id": "00000000-0000-4000-8000-000000000000",
            "kind": "original",
            "author_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1",
            "text": "this post only exists in the fake repository",
            "created_at": "2099-01-01T00:00:00.000Z",
            "reply_to_id": None,
            "repost_of_id": None,
        }]

    def get_user(self, user_id):
        return {
            "id": user_id, "handle": "fakeuser", "display_name": "Fake User",
            "bio": None, "avatar": {"small_url": "/fake-48.jpg", "large_url": "/fake-96.jpg"},
        }

    def get_media_for_post(self, post_id):
        return []

    def get_like_count(self, post_id):
        return 999  # deliberately unrealistic, to prove it's THIS repo's value being used

    def get_reply_count(self, post_id):
        return 0

    def is_liked_by(self, user_id, post_id):
        return False


def test_dependency_override_changes_feed_response(client):
    # Before override: real fixture data
    r = client.get("/feed?limit=5")
    real_text = r.json()["items"][0]["text"]
    assert real_text != "this post only exists in the fake repository"

    # Override: swap in the fake repository
    app.dependency_overrides[get_social_repository] = lambda: FakeRepository()

    try:
        r = client.get("/feed?limit=5")
        body = r.json()
        assert len(body["items"]) == 1
        assert body["items"][0]["text"] == "this post only exists in the fake repository"
        assert body["items"][0]["likeCount"] == 999
    finally:
        # Always reset overrides after the test — otherwise this fake
        # repository would silently leak into every test that runs after
        # this one in the same session.
        app.dependency_overrides.clear()

    # After clearing: back to real fixture data, proving the override
    # didn't permanently break anything.
    r = client.get("/feed?limit=5")
    assert r.json()["items"][0]["text"] == real_text