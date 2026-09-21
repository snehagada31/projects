"""
Like service: implements desired-state idempotent like/unlike operations.
"""
import inspect
from typing import Any
from app.common.errors import NotFoundError, ValidationError
from app.schemas.post import LikeResponse


async def maybe_await(val: Any) -> Any:
    if inspect.isawaitable(val):
        return await val
    return val


async def set_post_like(repo, post_id: str, viewer_id: str) -> LikeResponse:
    post = await maybe_await(repo.get_post(post_id))
    if not post:
        raise NotFoundError("post not found")

    kind = post["kind"] if isinstance(post, dict) else post.kind
    if kind == "repost":
        raise ValidationError(
            "liking a repost is not supported; like the original post instead",
            field="postId",
            reason="invalid_kind",
            status_code=422,
        )

    await maybe_await(repo.add_like(viewer_id, post_id))
    count = await maybe_await(repo.get_like_count(post_id))
    return LikeResponse(post_id=post_id, liked_by_viewer=True, like_count=count)


async def remove_post_like(repo, post_id: str, viewer_id: str) -> LikeResponse:
    post = await maybe_await(repo.get_post(post_id))
    if not post:
        raise NotFoundError("post not found")

    await maybe_await(repo.remove_like(viewer_id, post_id))
    count = await maybe_await(repo.get_like_count(post_id))
    return LikeResponse(post_id=post_id, liked_by_viewer=False, like_count=count)
