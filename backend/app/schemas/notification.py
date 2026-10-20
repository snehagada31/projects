"""
Notification response schemas for Stage 6 (PY-P0-06).
Matches camelCase API conventions across the platform.
"""

from pydantic import Field, ConfigDict
from app.schemas.base import CamelModel
from app.schemas.user import Avatar


class NotificationActor(CamelModel):
    id: str
    handle: str
    display_name: str = Field(alias="displayName")
    avatar: Avatar


class NotificationItem(CamelModel):
    id: str
    recipient_id: str = Field(alias="recipientId")
    actor: NotificationActor
    event_type: str = Field(alias="eventType")  # "like" | "reply" | "repost" | "follow"
    post_id: str | None = Field(default=None, alias="postId")
    is_read: bool = Field(alias="isRead")
    created_at: str = Field(alias="createdAt")


class UnreadCountResponse(CamelModel):
    count: int


class MarkAllReadResponse(CamelModel):
    marked_read: int = Field(alias="markedRead")
