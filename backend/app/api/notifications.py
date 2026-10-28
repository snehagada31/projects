"""
Notification endpoints for Stage 6 (PY-P0-06):
- GET /notifications: Paginated, reverse-chronological notification inbox for authenticated actor.
- GET /notifications/unread-count: Authoritative unread count.
- PATCH /notifications/{id}/read: Mark single notification as read (anti-IDOR protected).
- POST /notifications/read-all: Mark all unread notifications as read.
"""

import uuid
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.db.models import User, Notification
from app.repositories.postgres_repository import PostgresSocialRepository
from app.services.auth_service import get_current_user
from app.services.post_service import maybe_await
from app.common.errors import NotFoundError, AuthorizationError, ValidationError
from app.common.query_validation import validate_pagination_params
from app.common.pagination import paginate
from app.schemas.notification import (
    NotificationItem,
    NotificationActor,
    UnreadCountResponse,
    MarkAllReadResponse,
    NotificationPreferencesResponse,
    UpdateNotificationPreferencesRequest,
)
from app.schemas.user import Avatar
from app.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])


def get_social_repository(db: AsyncSession = Depends(get_db_session)) -> PostgresSocialRepository:
    return PostgresSocialRepository(db)


def _validate_uuid(val: str, field_name: str = "id") -> None:
    try:
        uuid.UUID(val)
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid UUID: {val}", field=field_name, reason="invalid_uuid", status_code=400)


def build_notification_item(notif: Notification) -> NotificationItem:
    actor = notif.actor
    if not actor or not actor.is_active:
        actor_summary = NotificationActor(
            id=str(notif.actor_id),
            handle="deactivated",
            display_name="[Deactivated User]",
            avatar=Avatar(small_url="/fixtures/default.jpg", large_url="/fixtures/default.jpg"),
        )
    else:
        actor_summary = NotificationActor(
            id=str(actor.id),
            handle=actor.handle,
            display_name=actor.display_name,
            avatar=Avatar(small_url=actor.avatar_small_url, large_url=actor.avatar_large_url),
        )

    created_iso = notif.created_at.isoformat() if notif.created_at else ""
    if created_iso.endswith("+00:00"):
        created_iso = created_iso[:-6] + "Z"

    return NotificationItem(
        id=str(notif.id),
        recipient_id=str(notif.recipient_id),
        actor=actor_summary,
        event_type=notif.event_type,
        post_id=str(notif.post_id) if notif.post_id else None,
        is_read=notif.is_read,
        created_at=created_iso,
    )


@router.get("", response_model=PaginatedResponse[NotificationItem])
async def list_notifications(
    request: Request,
    current_user: User = Depends(get_current_user),
    repo: PostgresSocialRepository = Depends(get_social_repository),
):
    cursor_tuple, limit = validate_pagination_params(request)
    notifs = await maybe_await(repo.get_notifications(str(current_user.id)))
    page, next_cursor, has_more = paginate(notifs, cursor_tuple, limit)
    items = [build_notification_item(n) for n in page]
    return PaginatedResponse(items=items, next_cursor=next_cursor, has_more=has_more)


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    repo: PostgresSocialRepository = Depends(get_social_repository),
):
    count = await maybe_await(repo.get_unread_notification_count(str(current_user.id)))
    return UnreadCountResponse(count=count)


@router.patch("/{notification_id}/read", response_model=NotificationItem)
async def mark_notification_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    repo: PostgresSocialRepository = Depends(get_social_repository),
):
    _validate_uuid(notification_id)
    res = await maybe_await(repo.mark_notification_read(notification_id, str(current_user.id)))
    if res is None:
        raise NotFoundError("Notification not found")
    if res == "FORBIDDEN":
        raise AuthorizationError("Cannot mark another user's notification as read")
    return build_notification_item(res)


@router.post("/read-all", response_model=MarkAllReadResponse)
async def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    repo: PostgresSocialRepository = Depends(get_social_repository),
):
    marked_count = await maybe_await(repo.mark_all_notifications_read(str(current_user.id)))
    return MarkAllReadResponse(marked_read=marked_count)



@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_preferences(
    current_user: User = Depends(get_current_user),
    repo: PostgresSocialRepository = Depends(get_social_repository),
):
    prefs = await repo.get_notification_preferences(str(current_user.id))
    return NotificationPreferencesResponse(**prefs)


@router.patch("/preferences", response_model=NotificationPreferencesResponse)
async def update_preferences(
    req: UpdateNotificationPreferencesRequest,
    current_user: User = Depends(get_current_user),
    repo: PostgresSocialRepository = Depends(get_social_repository),
):
    updated = await repo.update_notification_preferences(
        user_id=str(current_user.id),
        likes=req.likes,
        reposts=req.reposts,
        replies=req.replies,
        follows=req.follows,
    )
    return NotificationPreferencesResponse(**updated)
