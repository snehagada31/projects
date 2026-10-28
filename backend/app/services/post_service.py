"""
Post service: builds schema objects and validates business rules.
Supports both async (Postgres) and sync (Fixture) repositories transparently.
"""
import inspect
from typing import Any
from app.schemas.post import PostItem, MediaItem
from app.schemas.user import AuthorSummary, Avatar
from app.common.errors import ValidationError, NotFoundError, ConflictError


async def maybe_await(val: Any) -> Any:
    if inspect.isawaitable(val):
        return await val
    return val


async def build_post_item(repo, post: dict | Any, viewer_id: str | None = None) -> PostItem:
    """Builds a PostItem Pydantic schema from either a dict (fixture) or ORM model."""
    if isinstance(post, dict):
        post_id = str(post["id"])
        author = post.get("author")
        if not author and "author_id" in post:
            author = await maybe_await(repo.get_user(post["author_id"]))
    else:
        post_id = str(post.id)
        author = getattr(post, "author", None)
        if not author and hasattr(post, "author_id"):
            author = await maybe_await(repo.get_user(str(post.author_id)))

    if isinstance(author, dict):
        avatar_dict = author.get("avatar") or {}
        small_url = avatar_dict.get("small_url") or author.get("avatar_small_url", "")
        large_url = avatar_dict.get("large_url") or author.get("avatar_large_url", "")
        author_summary = AuthorSummary(
            id=str(author.get("id", "")),
            handle=author.get("handle", ""),
            display_name=author.get("display_name", ""),
            avatar=Avatar(small_url=small_url, large_url=large_url),
        )
    elif author is not None:
        author_summary = AuthorSummary(
            id=str(author.id),
            handle=author.handle,
            display_name=author.display_name,
            avatar=Avatar(small_url=author.avatar_small_url, large_url=author.avatar_large_url),
        )
    else:
        author_summary = AuthorSummary(
            id="",
            handle="unknown",
            display_name="Unknown",
            avatar=Avatar(small_url="", large_url=""),
        )

    raw_media = await maybe_await(repo.get_media_for_post(post_id))
    media_items = [
        MediaItem(
            id=str(m["id"] if isinstance(m, dict) else m.id),
            alt_text=m["alt_text"] if isinstance(m, dict) else m.alt_text,
            width=m["width"] if isinstance(m, dict) else m.width,
            height=m["height"] if isinstance(m, dict) else m.height,
            position=m["position"] if isinstance(m, dict) else m.position,
            small_url=m["small_url"] if isinstance(m, dict) else m.small_url,
            large_url=m["large_url"] if isinstance(m, dict) else m.large_url,
        )
        for m in raw_media
    ]

    kind = post["kind"] if isinstance(post, dict) else post.kind
    text = post.get("text") if isinstance(post, dict) else post.text
    created_at = post["created_at"] if isinstance(post, dict) else post.created_at
    if hasattr(created_at, "isoformat"):
        created_at_str = created_at.isoformat()
        if created_at_str.endswith("+00:00"):
            base = created_at_str[:-6]
            if "." not in base:
                created_at_str = f"{base}.000Z"
            else:
                created_at_str = f"{base}Z"
    else:
        created_at_str = str(created_at)

    reply_to_id = post.get("reply_to_id") if isinstance(post, dict) else getattr(post, "reply_to_id", None)
    repost_of_id = post.get("repost_of_id") if isinstance(post, dict) else getattr(post, "repost_of_id", None)

    like_count = await maybe_await(repo.get_like_count(post_id))
    reply_count = await maybe_await(repo.get_reply_count(post_id))
    liked_by_viewer = (await maybe_await(repo.is_liked_by(viewer_id, post_id))) if viewer_id else False

    retweet_count = (await maybe_await(repo.get_repost_count(post_id))) if hasattr(repo, "get_repost_count") else 0
    reposted_by_viewer = (await maybe_await(repo.is_reposted_by(viewer_id, post_id))) if (viewer_id and hasattr(repo, "is_reposted_by")) else False
    bookmarked_by_viewer = (await maybe_await(repo.is_bookmarked_by(viewer_id, post_id))) if (viewer_id and hasattr(repo, "is_bookmarked_by")) else False

    return PostItem(
        id=post_id,
        kind=kind,
        text=text,
        created_at=created_at_str,
        author=author_summary,
        media=media_items,
        like_count=like_count,
        reply_count=reply_count,
        liked_by_viewer=liked_by_viewer,
        reposted_by_viewer=reposted_by_viewer,
        bookmarked_by_viewer=bookmarked_by_viewer,
        retweet_count=retweet_count,
        reply_to_id=str(reply_to_id) if reply_to_id else None,
        repost_of_id=str(repost_of_id) if repost_of_id else None,
    )


async def validate_create_post_rules(
    repo,
    kind: str,
    text: str | None,
    reply_to_id: str | None,
    repost_of_id: str | None,
    author_id: str,
) -> tuple[str, str | None, str | None, str | None]:
    if kind not in ("original", "reply", "repost"):
        raise ValidationError("kind must be 'original', 'reply', or 'repost'", field="kind", reason="invalid_choice", status_code=422)

    trimmed_text = text.strip() if text is not None else None

    if kind == "original":
        if not trimmed_text or not (1 <= len(trimmed_text) <= 280):
            raise ValidationError("original text must be between 1 and 280 characters", field="text", reason="length", status_code=422)
        if reply_to_id is not None or repost_of_id is not None:
            raise ValidationError("original post cannot reference another post", field="kind", reason="invalid_combination", status_code=422)

    elif kind == "reply":
        if not trimmed_text or not (1 <= len(trimmed_text) <= 280):
            raise ValidationError("reply text must be between 1 and 280 characters", field="text", reason="length", status_code=422)
        if not reply_to_id:
            raise ValidationError("reply must specify replyToId", field="replyToId", reason="missing", status_code=422)
        if repost_of_id is not None:
            raise ValidationError("reply cannot specify repostOfId", field="repostOfId", reason="unexpected", status_code=422)

        target = await maybe_await(repo.get_post(reply_to_id))
        if not target:
            raise NotFoundError("referenced post not found")
        target_kind = target["kind"] if isinstance(target, dict) else target.kind
        if target_kind != "original":
            raise ValidationError("replies may only reference original posts", field="replyToId", reason="invalid_target_kind", status_code=422)

    elif kind == "repost":
        if trimmed_text:
            raise ValidationError("repost cannot contain text", field="text", reason="unexpected", status_code=422)
        if not repost_of_id:
            raise ValidationError("repost must specify repostOfId", field="repostOfId", reason="missing", status_code=422)
        if reply_to_id is not None:
            raise ValidationError("repost cannot specify replyToId", field="replyToId", reason="unexpected", status_code=422)

        target = await maybe_await(repo.get_post(repost_of_id))
        if not target:
            raise NotFoundError("referenced post not found")
        target_kind = target["kind"] if isinstance(target, dict) else target.kind
        if target_kind != "original":
            raise ValidationError("reposts may only reference original posts", field="repostOfId", reason="invalid_target_kind", status_code=422)

        if hasattr(repo, "has_user_reposted"):
            has_reposted = await maybe_await(repo.has_user_reposted(author_id, repost_of_id))
            if has_reposted:
                raise ConflictError("user has already reposted this original post")

    return kind, trimmed_text, reply_to_id, repost_of_id
