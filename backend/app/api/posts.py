"""
Post endpoints:
- GET /posts/{id}
- GET /posts/{id}/replies
- POST /posts
- PUT /posts/{id}/like
- DELETE /posts/{id}/like
- GET /search/posts
"""
import os
import base64
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request, status
from app.repositories.social_repository import SocialRepository
from app.api.feed import get_social_repository
from app.schemas.post import (
    PostItem,
    PostDetailResponse,
    ReferencedPost,
    CreatePostRequest,
    LikeResponse,
    RepostResponse,
    BookmarkResponse,
    EditPostRequest,
    ReportPostRequest,
    ReportPostResponse,
    ConversationResponse,
    ThreadPostItem,
)
from app.schemas.pagination import PaginatedResponse
from app.schemas.user import AuthorSummary, Avatar
from app.services.post_service import build_post_item, validate_create_post_rules, maybe_await
from app.services.like_service import set_post_like, remove_post_like
from app.services.auth_service import get_current_user, get_optional_current_user
from app.db.models import User
from app.common.errors import ValidationError, NotFoundError, AuthorizationError
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
async def get_post_detail(
    post_id: str,
    current_user: User | None = Depends(get_optional_current_user),
    repo: SocialRepository = Depends(get_social_repository),
):
    _validate_uuid(post_id)
    post = await maybe_await(repo.get_post(post_id))
    if not post:
        raise NotFoundError("post not found")

    viewer_id = str(current_user.id) if current_user else None
    item = await build_post_item(repo, post, viewer_id=viewer_id)
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
async def get_post_replies(
    post_id: str,
    request: Request,
    current_user: User | None = Depends(get_optional_current_user),
    repo: SocialRepository = Depends(get_social_repository),
):
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
    viewer_id = str(current_user.id) if current_user else None
    items = [await build_post_item(repo, r, viewer_id=viewer_id) for r in page]
    return PaginatedResponse(items=items, next_cursor=next_cursor, has_more=has_more)


@router.get("/posts/{post_id}/conversation", response_model=ConversationResponse)
async def get_conversation(
    post_id: str,
    reply_limit: int = 20,
    current_user: User | None = Depends(get_optional_current_user),
    repo: SocialRepository = Depends(get_social_repository),
):
    _validate_uuid(post_id)
    viewer_id = str(current_user.id) if current_user else None

    if hasattr(repo, "get_post_conversation"):
        conv = await maybe_await(repo.get_post_conversation(post_id, reply_limit=reply_limit))
    else:
        conv = None

    if not conv:
        raise NotFoundError("post not found")

    async def _to_thread_item(p) -> ThreadPostItem:
        if isinstance(p, dict) and p.get("is_deleted_parent"):
            return ThreadPostItem(
                id=str(p["id"]),
                kind="reply",
                text="[This post was deleted]",
                is_deleted_parent=True,
                author=None,
                created_at=None,
                media=[],
                reply_to_id=None,
            )
        item = await build_post_item(repo, p, viewer_id=viewer_id)
        return ThreadPostItem(
            id=item.id,
            kind=item.kind,
            text=item.text,
            created_at=item.created_at,
            author=item.author,
            media=item.media,
            like_count=item.like_count,
            reply_count=item.reply_count,
            retweet_count=item.retweet_count,
            liked_by_viewer=item.liked_by_viewer,
            reposted_by_viewer=item.reposted_by_viewer,
            bookmarked_by_viewer=item.bookmarked_by_viewer,
            reply_to_id=item.reply_to_id,
            is_deleted_parent=False,
        )

    focus_item = await _to_thread_item(conv["focus_post"])
    ancestor_items = [await _to_thread_item(a) for a in conv["ancestors"]]
    reply_items = [await _to_thread_item(r) for r in conv["replies"]]

    return ConversationResponse(
        root_id=conv["root_id"],
        focus_post=focus_item,
        ancestors=ancestor_items,
        replies=reply_items,
        reply_count=conv["reply_count"],
    )


@router.post("/posts", status_code=status.HTTP_201_CREATED)
async def create_post(
    payload: CreatePostRequest,
    current_user: User = Depends(get_current_user),
    repo: SocialRepository = Depends(get_social_repository),
):
    author_id = str(current_user.id)
    kind, text, reply_to_id, repost_of_id = await validate_create_post_rules(
        repo, payload.kind, payload.text, payload.reply_to_id, payload.repost_of_id, author_id
    )

    # PY-P1-05: Media publishing rules (<= 4 images, dimension bounds, non-empty alt text)
    if payload.media:
        if kind == "repost":
            raise ValidationError("Cannot attach media to a repost", field="media", reason="media_on_repost", status_code=422)
        if len(payload.media) > 4:
            raise ValidationError("Cannot attach more than 4 images", field="media", reason="max_images_exceeded", status_code=422)
        for idx, m in enumerate(payload.media):
            if not m.alt_text or not m.alt_text.strip():
                raise ValidationError("Alt text is required for each image", field=f"media[{idx}].alt_text", reason="missing_alt_text", status_code=422)
            if m.width <= 0 or m.height <= 0 or m.width > 8192 or m.height > 8192:
                raise ValidationError("Image dimensions must be positive and <= 8192", field=f"media[{idx}].dimensions", reason="invalid_dimensions", status_code=422)
            if not m.small_url or not m.large_url:
                raise ValidationError("Image URLs cannot be empty", field=f"media[{idx}].urls", reason="missing_url", status_code=422)

    new_post = await maybe_await(repo.create_post(
        author_id=author_id,
        kind=kind,
        text=text,
        reply_to_id=reply_to_id,
        repost_of_id=repost_of_id,
    ))

    if payload.media and hasattr(repo, "attach_media_to_post"):
        post_id_str = str(new_post["id"] if isinstance(new_post, dict) else new_post.id)
        await maybe_await(repo.attach_media_to_post(
            post_id_str,
            [m.model_dump() for m in payload.media]
        ))

    item = await build_post_item(repo, new_post, viewer_id=author_id)
    return {"item": item}


@router.post("/upload-image")
async def upload_image(
    request: Request,
    payload: dict,
    current_user: User = Depends(get_current_user),
):
    data = payload.get("data")
    filename = payload.get("filename", "image.jpg")
    if not data:
        raise ValidationError("Missing image data", field="data", reason="missing", status_code=422)

    if "," in data:
        data = data.split(",", 1)[1]

    try:
        binary_data = base64.b64decode(data)
    except Exception:
        raise ValidationError("Invalid base64 image data", field="data", reason="invalid_base64", status_code=422)

    if len(binary_data) > 10 * 1024 * 1024:
        raise ValidationError("Image too large (max 10MB)", field="data", reason="file_too_large", status_code=422)

    ext = os.path.splitext(filename)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
        ext = ".jpg"

    safe_name = f"{uuid.uuid4().hex}{ext}"
    uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))
    os.makedirs(uploads_dir, exist_ok=True)
    file_path = os.path.join(uploads_dir, safe_name)

    with open(file_path, "wb") as f:
        f.write(binary_data)

    base_url = str(request.base_url).rstrip("/")
    image_url = f"{base_url}/uploads/{safe_name}"
    return {"url": image_url}


@router.patch("/posts/{post_id}")
async def edit_post(
    post_id: str,
    payload: EditPostRequest,
    current_user: User = Depends(get_current_user),
    repo: SocialRepository = Depends(get_social_repository),
):
    _validate_uuid(post_id)
    post = await maybe_await(repo.get_post(post_id))
    if not post:
        raise NotFoundError("post not found")

    author_id_str = str(post["author_id"] if isinstance(post, dict) else post.author_id)
    if author_id_str != str(current_user.id):
        raise AuthorizationError("Only the author can edit this post")

    post_kind = post["kind"] if isinstance(post, dict) else post.kind
    if post_kind not in ("original", "reply"):
        raise ValidationError("Reposts cannot be edited", field="kind", reason="cannot_edit_repost", status_code=422)

    created_at = post.get("created_at") if isinstance(post, dict) else getattr(post, "created_at", None)
    if created_at:
        try:
            if isinstance(created_at, str):
                c_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            else:
                c_time = created_at
            if hasattr(c_time, "tzinfo") and c_time.tzinfo is None:
                c_time = c_time.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            if (now - c_time).total_seconds() > 15 * 60:
                raise ValidationError("Posts can only be edited within 15 minutes of posting", field="createdAt", reason="edit_window_expired", status_code=422)
        except ValidationError:
            raise
        except Exception:
            pass

    updated = await maybe_await(repo.update_post_text(post_id, payload.text))
    item = await build_post_item(repo, updated, viewer_id=str(current_user.id))
    return {"item": item}


@router.put("/posts/{post_id}/like", response_model=LikeResponse)
async def like_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    repo: SocialRepository = Depends(get_social_repository),
):
    _validate_uuid(post_id)
    return await set_post_like(repo, post_id, str(current_user.id))


@router.delete("/posts/{post_id}/like", response_model=LikeResponse)
async def unlike_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    repo: SocialRepository = Depends(get_social_repository),
):
    _validate_uuid(post_id)
    return await remove_post_like(repo, post_id, str(current_user.id))


@router.get("/search/posts", response_model=PaginatedResponse[PostItem])
async def search_posts(
    request: Request,
    current_user: User | None = Depends(get_optional_current_user),
    repo: SocialRepository = Depends(get_social_repository),
):
    q = request.query_params.get("q", "")
    trimmed = q.strip()
    if not (2 <= len(trimmed) <= 80):
        raise ValidationError("q must be between 2 and 80 characters", field="q", reason="out_of_range", status_code=400)

    cursor_tuple, limit = validate_pagination_params(request, allowed={"cursor", "limit", "q"})
    results = await maybe_await(repo.search_originals(trimmed))
    page, next_cursor, has_more = paginate(results, cursor_tuple, limit)
    viewer_id = str(current_user.id) if current_user else None
    items = [await build_post_item(repo, p, viewer_id=viewer_id) for p in page]
    return PaginatedResponse(items=items, next_cursor=next_cursor, has_more=has_more)


@router.put("/posts/{post_id}/repost", response_model=RepostResponse)
async def repost_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    repo: SocialRepository = Depends(get_social_repository),
):
    _validate_uuid(post_id)
    target = await maybe_await(repo.get_post(post_id))
    if not target:
        raise NotFoundError("post not found")
    target_kind = target["kind"] if isinstance(target, dict) else target.kind
    if target_kind != "original":
        raise ValidationError("reposts may only reference original posts", field="id", reason="invalid_target_kind", status_code=422)

    await maybe_await(repo.add_repost(str(current_user.id), post_id))
    retweet_count = await maybe_await(repo.get_repost_count(post_id))
    return RepostResponse(post_id=post_id, reposted_by_viewer=True, retweet_count=retweet_count)


@router.delete("/posts/{post_id}/repost", response_model=RepostResponse)
async def unrepost_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    repo: SocialRepository = Depends(get_social_repository),
):
    _validate_uuid(post_id)
    await maybe_await(repo.remove_repost(str(current_user.id), post_id))
    retweet_count = await maybe_await(repo.get_repost_count(post_id))
    return RepostResponse(post_id=post_id, reposted_by_viewer=False, retweet_count=retweet_count)


@router.delete("/posts/{post_id}")
async def delete_post_or_comment(
    post_id: str,
    current_user: User = Depends(get_current_user),
    repo: SocialRepository = Depends(get_social_repository),
):
    _validate_uuid(post_id)
    post = await maybe_await(repo.get_post(post_id))
    if not post:
        raise NotFoundError("post not found")

    author_id_str = str(post["author_id"] if isinstance(post, dict) else post.author_id)
    if author_id_str != str(current_user.id):
        raise AuthorizationError("Only the author can delete this post")

    deleted = await maybe_await(repo.delete_post(post_id))
    if not deleted:
        raise NotFoundError("post not found")
    return {"success": True, "deletedId": post_id}


@router.put("/posts/{post_id}/bookmark", response_model=BookmarkResponse)
async def bookmark_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    repo: SocialRepository = Depends(get_social_repository),
):
    _validate_uuid(post_id)
    target = await maybe_await(repo.get_post(post_id))
    if not target:
        raise NotFoundError("post not found")
    if hasattr(repo, "bookmark_post"):
        await repo.bookmark_post(str(current_user.id), post_id)
    return BookmarkResponse(post_id=post_id, bookmarked_by_viewer=True)


@router.delete("/posts/{post_id}/bookmark", response_model=BookmarkResponse)
async def unbookmark_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    repo: SocialRepository = Depends(get_social_repository),
):
    _validate_uuid(post_id)
    if hasattr(repo, "unbookmark_post"):
        await repo.unbookmark_post(str(current_user.id), post_id)
    return BookmarkResponse(post_id=post_id, bookmarked_by_viewer=False)


@router.get("/bookmarks", response_model=PaginatedResponse[PostItem])
async def list_bookmarks(
    request: Request,
    current_user: User = Depends(get_current_user),
    repo: SocialRepository = Depends(get_social_repository),
):
    cursor_tuple, limit = validate_pagination_params(request)
    posts = (
        await maybe_await(repo.get_bookmarked_posts(str(current_user.id)))
        if hasattr(repo, "get_bookmarked_posts")
        else []
    )
    page, next_cursor, has_more = paginate(posts, cursor_tuple, limit)
    viewer_id = str(current_user.id)
    items = [await build_post_item(repo, p, viewer_id=viewer_id) for p in page]
    return PaginatedResponse(items=items, next_cursor=next_cursor, has_more=has_more)






ALLOWED_REPORT_REASONS = {"spam", "harassment", "hate_speech", "misinformation"}


@router.post("/posts/{post_id}/report", response_model=ReportPostResponse)
async def report_post(
    post_id: str,
    req: ReportPostRequest,
    current_user: User = Depends(get_current_user),
    repo: SocialRepository = Depends(get_social_repository),
):
    _validate_uuid(post_id)
    target = await maybe_await(repo.get_post(post_id))
    if not target:
        raise NotFoundError("post not found")

    reason_lower = req.reason.strip().lower()
    if reason_lower not in ALLOWED_REPORT_REASONS:
        raise ValidationError(
            f"Invalid reason '{req.reason}'. Allowed: {', '.join(sorted(ALLOWED_REPORT_REASONS))}",
            field="reason",
            reason="invalid_choice",
            status_code=422,
        )

    if hasattr(repo, "create_post_report"):
        report_id, status_val = await repo.create_post_report(
            post_id=post_id,
            reporter_id=str(current_user.id),
            reason=reason_lower,
            notes=req.notes,
        )
    else:
        report_id, status_val = str(uuid.uuid4()), "pending"

    return ReportPostResponse(success=True, report_id=report_id, status=status_val)
