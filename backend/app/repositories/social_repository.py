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

    def get_posts_by_author(self, author_id: str, kind: str | None = None) -> list[dict]:
        res = [p for p in self.all_posts if p.get("author_id") == author_id]
        if kind:
            res = [p for p in res if p.get("kind") == kind]
        return sorted(res, key=lambda p: (p.get("created_at") or "", str(p["id"])), reverse=True)

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


    def search_users(self, q: str, limit: int = 20, cursor: str | None = None) -> tuple[list[dict], str | None, bool]:
        lowered = q.strip().lower()
        matched = [
            u for u in self.users
            if lowered in u.get("handle", "").lower() or lowered in u.get("display_name", "").lower()
        ]
        matched.sort(key=lambda u: (u.get("handle", ""), u.get("id", "")))
        has_more = len(matched) > limit
        page = matched[:limit]
        next_cursor = f"{page[-1]['handle']}::{page[-1]['id']}" if has_more else None
        return page, next_cursor, has_more

    def get_explainable_suggestions(self, viewer_id: str | None, limit: int = 5) -> list[dict]:
        candidates = [u for u in self.users if u.get("id") != viewer_id and not (viewer_id and self.is_following(viewer_id, u.get("id")))]
        res = []
        for u in candidates[:limit]:
            f_cnt = self.get_follower_count(u.get("id"))
            res.append({
                "user": u,
                "follower_count": f_cnt,
                "reason": "Popular in your network" if f_cnt > 0 else "Suggested for you"
            })
        return res

    def get_post_conversation(self, post_id: str, reply_limit: int = 20) -> dict | None:
        focus = self.get_post(post_id)
        if not focus:
            return None
        ancestors = []
        visited = {focus["id"]}
        curr = focus
        while curr.get("reply_to_id") and len(visited) <= 10:
            parent_id = curr["reply_to_id"]
            if parent_id in visited:
                break
            visited.add(parent_id)
            parent = self.get_post(parent_id)
            if not parent:
                ancestors.insert(0, {
                    "id": parent_id,
                    "kind": "reply",
                    "text": "[This post was deleted]",
                    "is_deleted_parent": True,
                    "author": None,
                    "created_at": None,
                    "media": [],
                    "reply_to_id": None,
                })
                break
            ancestors.insert(0, parent)
            curr = parent
        replies = [p for p in self.all_posts if p.get("reply_to_id") == post_id]
        replies.sort(key=lambda p: (p.get("created_at", ""), p.get("id", "")))
        root_id = ancestors[0]["id"] if ancestors else focus["id"]
        return {
            "root_id": root_id,
            "focus_post": focus,
            "ancestors": ancestors,
            "replies": replies[:reply_limit],
            "reply_count": len(replies),
        }

    def attach_media_to_post(self, post_id: str, media_items: list[dict]) -> list[dict]:
        added = []
        for idx, m in enumerate(media_items[:4]):
            entry = {
                "id": str(uuid.uuid4()),
                "post_id": post_id,
                "position": idx,
                "alt_text": m.get("alt_text", ""),
                "width": m.get("width", 800),
                "height": m.get("height", 600),
                "small_url": m.get("small_url", ""),
                "large_url": m.get("large_url", ""),
            }
            self.media.append(entry)
            added.append(entry)
        return added
