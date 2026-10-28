"""
SQLAlchemy declarative models — mirrors db-design/db/schema.sql exactly.

IMPORTANT: these are NOT the same thing as app/schemas/ (the Pydantic
response models) or app/models.py (the earlier illustrative OOP
classes). Three different things, three different jobs:
  - app/models.py       — the Topic 12 exercise (Post/__len__/__eq__), unrelated to DB
  - app/db/models.py     — THIS file — maps to real database TABLES
  - app/schemas/          — what actually goes out over HTTP (camelCase JSON)

Routes/services must never return one of these SQLAlchemy objects
directly as a response — they get converted to a Pydantic schema first,
inside the session's lifetime, before the session closes.
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Text, Integer, Boolean, ForeignKey, CheckConstraint, UniqueConstraint

from sqlalchemy import text as sql_text
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=sql_text("gen_random_uuid()"))
    handle: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_small_url: Mapped[str] = mapped_column(Text, nullable=False)
    avatar_large_url: Mapped[str] = mapped_column(Text, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sql_text("true"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True, precision=3), nullable=False, server_default=sql_text("now()"))


    __table_args__ = (

        CheckConstraint("handle = lower(handle)", name="handle_is_lowercase"),
        CheckConstraint("length(trim(handle)) > 0", name="handle_not_empty"),
    )


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=sql_text("gen_random_uuid()"))
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True, precision=3), nullable=False, server_default=sql_text("now()"))
    reply_to_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("posts.id", ondelete="RESTRICT"), nullable=True)
    repost_of_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("posts.id", ondelete="RESTRICT"), nullable=True)

    author: Mapped["User"] = relationship(foreign_keys=[author_id])

    __table_args__ = (
        CheckConstraint("kind IN ('original', 'reply', 'repost')", name="kind_is_valid"),
        CheckConstraint(
            "(kind = 'original' AND text IS NOT NULL AND reply_to_id IS NULL AND repost_of_id IS NULL) "
            "OR (kind = 'reply' AND text IS NOT NULL AND reply_to_id IS NOT NULL AND repost_of_id IS NULL) "
            "OR (kind = 'repost' AND text IS NULL AND reply_to_id IS NULL AND repost_of_id IS NOT NULL)",
            name="kind_shape_check",
        ),
        CheckConstraint("text IS NULL OR char_length(text) BETWEEN 1 AND 280", name="text_length_check"),
    )


class PostMedia(Base):
    __tablename__ = "post_media"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=sql_text("gen_random_uuid()"))
    post_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    alt_text: Mapped[str] = mapped_column(Text, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    small_url: Mapped[str] = mapped_column(Text, nullable=False)
    large_url: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True, precision=3), nullable=False, server_default=sql_text("now()"))

    __table_args__ = (
        CheckConstraint("width > 0", name="width_positive"),
        CheckConstraint("height > 0", name="height_positive"),
        CheckConstraint("length(trim(alt_text)) > 0", name="alt_text_present"),
        CheckConstraint("length(small_url) > 0", name="small_url_present"),
        CheckConstraint("length(large_url) > 0", name="large_url_present"),
        CheckConstraint("position BETWEEN 0 AND 3", name="position_in_range"),
        UniqueConstraint("post_id", "position", name="unique_position_per_post"),
    )


class Like(Base):
    __tablename__ = "likes"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    post_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True, precision=3), nullable=False, server_default=sql_text("now()"))


class Follow(Base):
    __tablename__ = "follows"

    follower_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    following_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True, precision=3), nullable=False, server_default=sql_text("now()"))

    __table_args__ = (
        CheckConstraint("follower_id <> following_id", name="no_self_follow"),
    )


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=sql_text("gen_random_uuid()"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True, precision=3), nullable=False, server_default=sql_text("now()"))
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True, precision=3), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True, precision=3), nullable=True)

    user: Mapped["User"] = relationship(foreign_keys=[user_id])


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=sql_text("gen_random_uuid()"))
    recipient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    post_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("posts.id", ondelete="SET NULL"), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sql_text("false"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True, precision=3), nullable=False, server_default=sql_text("now()"))
    dedup_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)

    recipient: Mapped["User"] = relationship("User", foreign_keys=[recipient_id])
    actor: Mapped["User"] = relationship("User", foreign_keys=[actor_id])
    post: Mapped["Post"] = relationship("Post", foreign_keys=[post_id])


class Bookmark(Base):
    __tablename__ = "bookmarks"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    post_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True, precision=3), nullable=False, server_default=sql_text("now()"))

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    post: Mapped["Post"] = relationship("Post", foreign_keys=[post_id])


class UserNotificationPreference(Base):
    __tablename__ = "user_notification_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    likes: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sql_text("true"))
    reposts: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sql_text("true"))
    replies: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sql_text("true"))
    follows: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sql_text("true"))

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])


class PostReport(Base):
    __tablename__ = "post_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=sql_text("gen_random_uuid()"))
    post_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    reporter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reason: Mapped[str] = mapped_column(String(32), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=sql_text("'pending'"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True, precision=3), nullable=False, server_default=sql_text("now()"))

    post: Mapped["Post"] = relationship("Post", foreign_keys=[post_id])
    reporter: Mapped["User"] = relationship("User", foreign_keys=[reporter_id])
