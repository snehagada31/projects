"""
Post endpoints:
- GET /posts/{id}
- GET /posts/{id}/replies
- POST /posts
- PUT /posts/{id}/like
- DELETE /posts/{id}/like
- GET /search/posts
"""
import uuid
from fastapi import APIRouter, Depends, Request, status
from app.repositories.social_repository import SocialRepository
from app.api.feed import get_social_repository
from app.schemas.post import PostItem, PostDetailResponse, ReferencedPost, CreatePostRequest, LikeResponse
from app.schemas.pagination import PaginatedResponse
from app.schemas.user import AuthorSummary, Avatar
from app.services.post_service import build_post_item, validate_create_post_rules, maybe_await
from app.services.like_service import set_post_like, remove_post_like
from app.common.errors import ValidationError, NotFoundError
from app.common.query_validation import validate_pagination_params
from app.common.pagination import paginate
from app.config import settings

router = APIRouter()


def _validate_uuid(val: str, field_name: str = "id") -> str:
    try:
        uuid.UUID(val)
        return val
    except ValueError:
        raise ValidationError(f"{field_name} is not a valid UUID", field=field_name, reason="bad_uuid", status_code=400)


@router.get("/posts/{post_id}", response_model=PostDetailResponse)
async def get_post_detail(post_id: str, repo: SocialRepository = Depends(get_social_repository)):
    _validate_uuid(post_id)
    post = await maybe_await(repo.get_post(post_id))
    if not post:
        raise NotFoundError("post not found")

    item = await build_post_item(repo, post, viewer_id=settings.demo_user_id)
    referenced = None

    if item.kind == "repost" and item.repost_of_id:
        ref_target = await maybe_await(repo.get_post(item.repost_of_id))
        if ref_target:
            if isinstance(ref_target, dict):
                author = ref_target.get("author") or (await maybe_await(repo.get_user(ref_target.get("author_id"))))
                ref_id = str(ref_target["id"])
                ref_text = ref_target.get("text")
            else:
                author = getattr(ref_target, "author", None)
                if not author and hasattr(ref_target, "author_id"):
                    author = await maybe_await(repo.get_user(str(ref_target.author_id)))
                ref_id = str(ref_target.id)
                ref_text = ref_target.text

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
                author_summary = AuthorSummary(id="", handle="unknown", display_name="Unknown", avatar=Avatar(small_url="", large_url=""))

            referenced = ReferencedPost(
                id=ref_id,
                text=ref_text,
                author=author_summary,
            )

    return PostDetailResponse(item=item, referenced_post=referenced)


@router.get("/posts/{post_id}/replies", response_model=PaginatedResponse[PostItem])
async def get_post_replies(post_id: str, request: Request, repo: SocialRepository = Depends(get_social_repository)):
    _validate_uuid(post_id)
    target = await maybe_await(repo.get_post(post_id))
    if not target:
        raise NotFoundError("post not found")
    target_kind = target["kind"] if isinstance(target, dict) else target.kind
    if target_kind != "original":
        raise ValidationError("replies only exist for original posts", field="id", reason="invalid_kind", status_code=422)

    cursor_tuple, limit = validate_pagination_params(request)
    replies = await maybe_await(repo.get_replies_for_post(post_id))
    page, next_cursor, has_more = paginate(replies, cursor_tuple, limit)
    items = [await build_post_item(repo, r, viewer_id=settings.demo_user_id) for r in page]
    return PaginatedResponse(items=items, next_cursor=next_cursor, has_more=has_more)


@router.post("/posts", status_code=status.HTTP_201_CREATED)
async def create_post(payload: CreatePostRequest, repo: SocialRepository = Depends(get_social_repository)):
    author_id = settings.demo_user_id
    kind, text, reply_to_id, repost_of_id = await validate_create_post_rules(
        repo, payload.kind, payload.text, payload.reply_to_id, payload.repost_of_id, author_id
    )
    new_post = await maybe_await(repo.create_post(
        author_id=author_id,
        kind=kind,
        text=text,
        reply_to_id=reply_to_id,
        repost_of_id=repost_of_id,
    ))
    item = await build_post_item(repo, new_post, viewer_id=author_id)
    return {"item": item}


@router.put("/posts/{post_id}/like", response_model=LikeResponse)
async def like_post(post_id: str, repo: SocialRepository = Depends(get_social_repository)):
    _validate_uuid(post_id)
    return await set_post_like(repo, post_id, settings.demo_user_id)


@router.delete("/posts/{post_id}/like", response_model=LikeResponse)
async def unlike_post(post_id: str, repo: SocialRepository = Depends(get_social_repository)):
    _validate_uuid(post_id)
    return await remove_post_like(repo, post_id, settings.demo_user_id)


@router.get("/search/posts", response_model=PaginatedResponse[PostItem])
async def search_posts(request: Request, repo: SocialRepository = Depends(get_social_repository)):
    q = request.query_params.get("q", "")
    trimmed = q.strip()
    if not (2 <= len(trimmed) <= 80):
        raise ValidationError("q must be between 2 and 80 characters", field="q", reason="out_of_range", status_code=400)

    cursor_tuple, limit = validate_pagination_params(request, allowed={"cursor", "limit", "q"})
    results = await maybe_await(repo.search_originals(trimmed))
    page, next_cursor, has_more = paginate(results, cursor_tuple, limit)
    items = [await build_post_item(repo, p, viewer_id=settings.demo_user_id) for p in page]
    return PaginatedResponse(items=items, next_cursor=next_cursor, has_more=has_more)


from app.schemas.post import RepostResponse


@router.put("/posts/{post_id}/repost", response_model=RepostResponse)
async def repost_post(post_id: str, repo: SocialRepository = Depends(get_social_repository)):
    _validate_uuid(post_id)
    target = await maybe_await(repo.get_post(post_id))
    if not target:
        raise NotFoundError("post not found")
    target_kind = target["kind"] if isinstance(target, dict) else target.kind
    if target_kind != "original":
        raise ValidationError("reposts may only reference original posts", field="id", reason="invalid_target_kind", status_code=422)

    await maybe_await(repo.add_repost(settings.demo_user_id, post_id))
    retweet_count = await maybe_await(repo.get_repost_count(post_id))
    return RepostResponse(post_id=post_id, reposted_by_viewer=True, retweet_count=retweet_count)


@router.delete("/posts/{post_id}/repost", response_model=RepostResponse)
async def unrepost_post(post_id: str, repo: SocialRepository = Depends(get_social_repository)):
    _validate_uuid(post_id)
    await maybe_await(repo.remove_repost(settings.demo_user_id, post_id))
    retweet_count = await maybe_await(repo.get_repost_count(post_id))
    return RepostResponse(post_id=post_id, reposted_by_viewer=False, retweet_count=retweet_count)


@router.delete("/posts/{post_id}")
async def delete_post_or_comment(post_id: str, repo: SocialRepository = Depends(get_social_repository)):
    _validate_uuid(post_id)
    deleted = await maybe_await(repo.delete_post(post_id))
    if not deleted:
        raise NotFoundError("post not found")
    return {"success": True, "deletedId": post_id}

