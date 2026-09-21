"""
SocialRepository interface and FixtureSocialRepository implementation.
Supports both Stage A fixture reads and Stage C writes/extensions.
"""

import uuid
from datetime import datetime, timezone
from typing import Protocol
from app.fixtures.social_fixtures import USERS, ALL_POSTS, ORIGINALS, REPOSTS, REPLIES, MEDIA, LIKES, FOLLOWS


class SocialRepository(Protocol):
    def get_user(self, user_id: str) -> dict | None: ...
    def get_post(self, post_id: str) -> dict | None: ...
    def get_originals_sorted(self) -> list[dict]: ...
    def get_replies_for_post(self, post_id: str) -> list[dict]: ...
    def get_media_for_post(self, post_id: str) -> list[dict]: ...
    def get_like_count(self, post_id: str) -> int: ...
    def get_reply_count(self, post_id: str) -> int: ...
    def is_liked_by(self, user_id: str | None, post_id: str) -> bool: ...
    def get_post_count(self, user_id: str) -> int: ...
    def get_follower_count(self, user_id: str) -> int: ...
    def get_following_count(self, user_id: str) -> int: ...
    def add_like(self, user_id: str, post_id: str) -> None: ...
    def remove_like(self, user_id: str, post_id: str) -> None: ...
    def has_user_reposted(self, user_id: str, original_id: str) -> bool: ...
    def create_post(self, author_id: str, kind: str, text: str | None, reply_to_id: str | None, repost_of_id: str | None) -> dict: ...
    def search_originals(self, query: str) -> list[dict]: ...
    def get_user_media(self, user_id: str) -> list[dict]: ...


class FixtureSocialRepository:
    """Backed entirely by the in-memory fixtures — no database yet."""

    def __init__(self):
        self.users = list(USERS)
        self.all_posts = list(ALL_POSTS)
        self.originals = list(ORIGINALS)
        self.media = list(MEDIA)
        self.likes = list(LIKES)
        self.follows = list(FOLLOWS)

    def get_user(self, user_id: str) -> dict | None:
        for u in self.users:
            if u["id"] == user_id:
                return u
        return None

    def get_post(self, post_id: str) -> dict | None:
        for p in self.all_posts:
            if p["id"] == post_id:
                return p
        return None

    def get_originals_sorted(self) -> list[dict]:
        return sorted(self.originals, key=lambda p: (p["created_at"], p["id"]), reverse=True)

    def get_replies_for_post(self, post_id: str) -> list[dict]:
        replies = [p for p in self.all_posts if p.get("reply_to_id") == post_id]
        return sorted(replies, key=lambda p: (p["created_at"], p["id"]), reverse=True)

    def get_media_for_post(self, post_id: str) -> list[dict]:
        items = [m for m in self.media if m["post_id"] == post_id]
        return sorted(items, key=lambda m: m["position"])

    def get_like_count(self, post_id: str) -> int:
        return sum(1 for l in self.likes if l["post_id"] == post_id)

    def get_reply_count(self, post_id: str) -> int:
        return sum(1 for p in self.all_posts if p.get("reply_to_id") == post_id)

    def is_liked_by(self, user_id: str | None, post_id: str) -> bool:
        if not user_id:
            return False
        return any(l["user_id"] == user_id and l["post_id"] == post_id for l in self.likes)

    def get_post_count(self, user_id: str) -> int:
        return sum(1 for p in self.originals if p["author_id"] == user_id)

    def get_follower_count(self, user_id: str) -> int:
        return sum(1 for f in self.follows if f["following_id"] == user_id)

    def get_following_count(self, user_id: str) -> int:
        return sum(1 for f in self.follows if f["follower_id"] == user_id)

    def add_like(self, user_id: str, post_id: str) -> None:
        if not self.is_liked_by(user_id, post_id):
            self.likes.append({"user_id": user_id, "post_id": post_id})

    def remove_like(self, user_id: str, post_id: str) -> None:
        self.likes = [l for l in self.likes if not (l["user_id"] == user_id and l["post_id"] == post_id)]

    def has_user_reposted(self, user_id: str, original_id: str) -> bool:
        return any(
            p.get("kind") == "repost" and p.get("author_id") == user_id and p.get("repost_of_id") == original_id
            for p in self.all_posts
        )

    def create_post(self, author_id: str, kind: str, text: str | None, reply_to_id: str | None, repost_of_id: str | None) -> dict:
        author = self.get_user(author_id)
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        new_post = {
            "id": str(uuid.uuid4()),
            "author_id": author_id,
            "kind": kind,
            "text": text,
            "created_at": now_str,
            "reply_to_id": reply_to_id,
            "repost_of_id": repost_of_id,
            "author": author,
        }
        self.all_posts.append(new_post)
        if kind == "original":
            self.originals.append(new_post)
        return new_post

    def search_originals(self, query: str) -> list[dict]:
        lowered = query.lower()
        matched = []
        for p in self.originals:
            text_match = p.get("text") and lowered in p["text"].lower()
            author = p.get("author") or self.get_user(p.get("author_id", ""))
            author_match = False
            if author:
                author_match = (
                    lowered in author.get("handle", "").lower()
                    or lowered in author.get("display_name", "").lower()
                )
            if text_match or author_match:
                matched.append(p)
        return sorted(matched, key=lambda p: (p["created_at"], p["id"]), reverse=True)

    def get_user_media(self, user_id: str) -> list[dict]:
        user_original_ids = {p["id"] for p in self.originals if p["author_id"] == user_id}
        media_list = [m for m in self.media if m["post_id"] in user_original_ids]
        return sorted(media_list, key=lambda m: (m["created_at"], m["id"]), reverse=True)

    def get_repost_count(self, post_id: str) -> int:
        return sum(1 for p in self.all_posts if p.get("kind") == "repost" and p.get("repost_of_id") == post_id)

    def is_reposted_by(self, user_id: str | None, post_id: str) -> bool:
        if not user_id:
            return False
        return any(
            p.get("kind") == "repost" and p.get("author_id") == user_id and p.get("repost_of_id") == post_id
            for p in self.all_posts
        )

    def add_repost(self, user_id: str, original_id: str) -> dict:
        if self.is_reposted_by(user_id, original_id):
            for p in self.all_posts:
                if p.get("kind") == "repost" and p.get("author_id") == user_id and p.get("repost_of_id") == original_id:
                    return p
        return self.create_post(author_id=user_id, kind="repost", text=None, reply_to_id=None, repost_of_id=original_id)

    def remove_repost(self, user_id: str, original_id: str) -> None:
        self.all_posts = [
            p for p in self.all_posts
            if not (p.get("kind") == "repost" and p.get("author_id") == user_id and p.get("repost_of_id") == original_id)
        ]

    def delete_post(self, post_id: str) -> bool:
        initial_len = len(self.all_posts)
        self.all_posts = [p for p in self.all_posts if p["id"] != post_id]
        self.originals = [p for p in self.originals if p["id"] != post_id]
        return len(self.all_posts) < initial_len

    def is_following(self, follower_id: str, following_id: str) -> bool:
        return any(f["follower_id"] == follower_id and f["following_id"] == following_id for f in self.follows)

    def add_follow(self, follower_id: str, following_id: str) -> None:
        if follower_id != following_id and not self.is_following(follower_id, following_id):
            self.follows.append({"follower_id": follower_id, "following_id": following_id})

    def remove_follow(self, follower_id: str, following_id: str) -> None:
        self.follows = [f for f in self.follows if not (f["follower_id"] == follower_id and f["following_id"] == following_id)]

    def get_all_users(self) -> list[dict]:
        return list(self.users)