"""
PostgreSQL implementation of SocialRepository (Stage C).
"""

import uuid
from datetime import datetime
from sqlalchemy import select, func, and_, or_, desc, delete, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models import User, Post, PostMedia, Like, Follow, UserSession, Notification



class PostgresSocialRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user(self, user_id: str) -> dict | None:
        try:
            uid = uuid.UUID(user_id)
        except (ValueError, TypeError):
            return None
        stmt = select(User).where(and_(User.id == uid, User.is_active.is_(True)))
        res = await self.session.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            return None
        return {
            "id": str(user.id),
            "handle": user.handle,
            "display_name": user.display_name,
            "bio": user.bio,
            "avatar": {"small_url": user.avatar_small_url, "large_url": user.avatar_large_url},
        }


    async def get_post(self, post_id: str) -> Post | None:
        stmt = select(Post).options(selectinload(Post.author)).where(Post.id == uuid.UUID(post_id))
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_originals_sorted(self) -> list[Post]:
        stmt = (
            select(Post)
            .options(selectinload(Post.author))
            .join(User, Post.author_id == User.id)
            .where(and_(Post.kind == "original", User.is_active.is_(True)))
            .order_by(desc(Post.created_at), desc(Post.id))
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_personalized_feed(self, viewer_id: uuid.UUID | str) -> list[Post]:
        uid = uuid.UUID(str(viewer_id)) if isinstance(viewer_id, str) else viewer_id
        followed_subquery = select(Follow.following_id).where(Follow.follower_id == uid)

        stmt = (
            select(Post)
            .options(selectinload(Post.author))
            .join(User, Post.author_id == User.id)
            .where(
                and_(
                    Post.kind == "original",
                    User.is_active.is_(True),
                    or_(
                        Post.author_id.in_(followed_subquery),
                        Post.author_id == uid,
                    ),
                )
            )
            .order_by(desc(Post.created_at), desc(Post.id))
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())


    async def get_replies_for_post(self, post_id: str) -> list[Post]:
        stmt = (
            select(Post)
            .options(selectinload(Post.author))
            .where(Post.reply_to_id == uuid.UUID(post_id))
            .order_by(desc(Post.created_at), desc(Post.id))
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_media_for_post(self, post_id: str) -> list[PostMedia]:
        stmt = (
            select(PostMedia)
            .where(PostMedia.post_id == uuid.UUID(post_id))
            .order_by(PostMedia.position)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_like_count(self, post_id: str) -> int:
        stmt = select(func.count(Like.user_id)).where(Like.post_id == uuid.UUID(post_id))
        res = await self.session.execute(stmt)
        return res.scalar() or 0

    async def get_reply_count(self, post_id: str) -> int:
        stmt = select(func.count(Post.id)).where(Post.reply_to_id == uuid.UUID(post_id))
        res = await self.session.execute(stmt)
        return res.scalar() or 0

    async def is_liked_by(self, user_id: str | None, post_id: str) -> bool:
        if not user_id:
            return False
        stmt = select(Like).where(Like.user_id == uuid.UUID(user_id), Like.post_id == uuid.UUID(post_id))
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none() is not None

    async def get_post_count(self, user_id: str) -> int:
        stmt = select(func.count(Post.id)).where(Post.author_id == uuid.UUID(user_id), Post.kind == "original")
        res = await self.session.execute(stmt)
        return res.scalar() or 0

    async def get_follower_count(self, user_id: str) -> int:
        stmt = select(func.count(Follow.follower_id)).where(Follow.following_id == uuid.UUID(user_id))
        res = await self.session.execute(stmt)
        return res.scalar() or 0

    async def get_following_count(self, user_id: str) -> int:
        stmt = select(func.count(Follow.following_id)).where(Follow.follower_id == uuid.UUID(user_id))
        res = await self.session.execute(stmt)
        return res.scalar() or 0

    async def add_like(self, user_id: str, post_id: str) -> None:
        p_uuid = uuid.UUID(post_id)
        u_uuid = uuid.UUID(user_id)
        stmt = insert(Like).values(user_id=u_uuid, post_id=p_uuid).on_conflict_do_nothing()
        await self.session.execute(stmt)

        # Trigger notification to target post author if not self-like
        post_author_id = await self.session.scalar(select(Post.author_id).where(Post.id == p_uuid))
        if post_author_id and post_author_id != u_uuid:
            dedup = f"like:{user_id}:{post_id}"
            notif_stmt = insert(Notification).values(
                recipient_id=post_author_id,
                actor_id=u_uuid,
                event_type="like",
                post_id=p_uuid,
                dedup_key=dedup,
            ).on_conflict_do_nothing()
            await self.session.execute(notif_stmt)

        await self.session.commit()

    async def remove_like(self, user_id: str, post_id: str) -> None:
        p_uuid = uuid.UUID(post_id)
        u_uuid = uuid.UUID(user_id)
        stmt = delete(Like).where(Like.user_id == u_uuid, Like.post_id == p_uuid)
        await self.session.execute(stmt)

        dedup = f"like:{user_id}:{post_id}"
        await self.session.execute(delete(Notification).where(Notification.dedup_key == dedup))
        await self.session.commit()

    async def has_user_reposted(self, user_id: str, original_id: str) -> bool:
        stmt = select(Post).where(
            Post.author_id == uuid.UUID(user_id),
            Post.repost_of_id == uuid.UUID(original_id),
            Post.kind == "repost",
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none() is not None

    async def create_post(
        self, author_id: str, kind: str, text: str | None, reply_to_id: str | None, repost_of_id: str | None
    ) -> Post:
        u_uuid = uuid.UUID(author_id)
        new_post = Post(
            author_id=u_uuid,
            kind=kind,
            text=text,
            reply_to_id=uuid.UUID(reply_to_id) if reply_to_id else None,
            repost_of_id=uuid.UUID(repost_of_id) if repost_of_id else None,
        )
        self.session.add(new_post)
        await self.session.flush()

        # Trigger notification if this is a reply to another user's post
        if kind == "reply" and new_post.reply_to_id:
            parent_author_id = await self.session.scalar(
                select(Post.author_id).where(Post.id == new_post.reply_to_id)
            )
            if parent_author_id and parent_author_id != u_uuid:
                dedup = f"reply:{new_post.id}"
                notif = Notification(
                    recipient_id=parent_author_id,
                    actor_id=u_uuid,
                    event_type="reply",
                    post_id=new_post.id,
                    dedup_key=dedup,
                )
                self.session.add(notif)

        await self.session.commit()
        await self.session.refresh(new_post, ["author"])
        return new_post

    async def search_originals(self, query: str) -> list[Post]:
        # Escape SQL wildcards % and _
        escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        stmt = (
            select(Post)
            .join(User, Post.author_id == User.id)
            .options(selectinload(Post.author))
            .where(
                Post.kind == "original",
                or_(
                    Post.text.ilike(pattern, escape="\\"),
                    User.handle.ilike(pattern, escape="\\"),
                    User.display_name.ilike(pattern, escape="\\"),
                ),
            )
            .order_by(desc(Post.created_at), desc(Post.id))
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_user_media(self, user_id: str) -> list[PostMedia]:
        stmt = (
            select(PostMedia)
            .join(Post, Post.id == PostMedia.post_id)
            .where(Post.author_id == uuid.UUID(user_id), Post.kind == "original")
            .order_by(desc(PostMedia.created_at), desc(PostMedia.id))
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_repost_count(self, post_id: str) -> int:
        stmt = select(func.count(Post.id)).where(Post.repost_of_id == uuid.UUID(post_id), Post.kind == "repost")
        res = await self.session.execute(stmt)
        return res.scalar() or 0

    async def is_reposted_by(self, user_id: str | None, post_id: str) -> bool:
        if not user_id:
            return False
        stmt = select(Post).where(
            Post.author_id == uuid.UUID(user_id),
            Post.repost_of_id == uuid.UUID(post_id),
            Post.kind == "repost",
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none() is not None

    async def add_repost(self, user_id: str, original_id: str) -> Post:
        stmt = select(Post).where(
            Post.author_id == uuid.UUID(user_id),
            Post.repost_of_id == uuid.UUID(original_id),
            Post.kind == "repost",
        )
        res = await self.session.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            return existing

        new_repost = Post(
            author_id=uuid.UUID(user_id),
            kind="repost",
            text=None,
            reply_to_id=None,
            repost_of_id=uuid.UUID(original_id),
        )
        self.session.add(new_repost)

        # Trigger notification to original post author if not self-repost
        orig_author_id = await self.session.scalar(
            select(Post.author_id).where(Post.id == uuid.UUID(original_id))
        )
        if orig_author_id and orig_author_id != uuid.UUID(user_id):
            dedup = f"repost:{user_id}:{original_id}"
            notif_stmt = insert(Notification).values(
                recipient_id=orig_author_id,
                actor_id=uuid.UUID(user_id),
                event_type="repost",
                post_id=uuid.UUID(original_id),
                dedup_key=dedup,
            ).on_conflict_do_nothing()
            await self.session.execute(notif_stmt)

        await self.session.commit()
        await self.session.refresh(new_repost, ["author"])
        return new_repost

    async def remove_repost(self, user_id: str, original_id: str) -> None:
        stmt = delete(Post).where(
            Post.author_id == uuid.UUID(user_id),
            Post.repost_of_id == uuid.UUID(original_id),
            Post.kind == "repost",
        )
        await self.session.execute(stmt)

        dedup = f"repost:{user_id}:{original_id}"
        await self.session.execute(delete(Notification).where(Notification.dedup_key == dedup))
        await self.session.commit()

    async def update_post_text(self, post_id: str, new_text: str) -> Post | None:
        stmt = select(Post).options(selectinload(Post.author)).where(Post.id == uuid.UUID(post_id))
        res = await self.session.execute(stmt)
        post = res.scalar_one_or_none()
        if not post:
            return None
        post.text = new_text
        await self.session.commit()
        await self.session.refresh(post)
        return post

    async def delete_post(self, post_id: str) -> bool:
        stmt = select(Post).where(Post.id == uuid.UUID(post_id))

        res = await self.session.execute(stmt)
        post = res.scalar_one_or_none()
        if not post:
            return False
        await self.session.execute(delete(Like).where(Like.post_id == post.id))
        await self.session.execute(delete(PostMedia).where(PostMedia.post_id == post.id))
        await self.session.execute(delete(Post).where(Post.reply_to_id == post.id))
        await self.session.execute(delete(Post).where(Post.repost_of_id == post.id))
        await self.session.delete(post)
        await self.session.commit()
        return True

    async def is_following(self, follower_id: str, following_id: str) -> bool:
        stmt = select(Follow).where(
            Follow.follower_id == uuid.UUID(follower_id),
            Follow.following_id == uuid.UUID(following_id),
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none() is not None

    async def add_follow(self, follower_id: str, following_id: str) -> None:
        if follower_id == following_id:
            return
        fl_uuid = uuid.UUID(follower_id)
        fg_uuid = uuid.UUID(following_id)
        stmt = insert(Follow).values(
            follower_id=fl_uuid,
            following_id=fg_uuid,
        ).on_conflict_do_nothing()
        await self.session.execute(stmt)

        # Trigger notification to following_id
        dedup = f"follow:{follower_id}:{following_id}"
        notif_stmt = insert(Notification).values(
            recipient_id=fg_uuid,
            actor_id=fl_uuid,
            event_type="follow",
            post_id=None,
            dedup_key=dedup,
        ).on_conflict_do_nothing()
        await self.session.execute(notif_stmt)

        await self.session.commit()

    async def remove_follow(self, follower_id: str, following_id: str) -> None:
        stmt = delete(Follow).where(
            Follow.follower_id == uuid.UUID(follower_id),
            Follow.following_id == uuid.UUID(following_id),
        )
        await self.session.execute(stmt)

        dedup = f"follow:{follower_id}:{following_id}"
        await self.session.execute(delete(Notification).where(Notification.dedup_key == dedup))
        await self.session.commit()

    async def get_followers(self, user_id: str) -> list[User]:
        stmt = (
            select(User)
            .join(Follow, Follow.follower_id == User.id)
            .where(and_(Follow.following_id == uuid.UUID(user_id), User.is_active.is_(True)))
            .order_by(Follow.created_at.desc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_following(self, user_id: str) -> list[User]:
        stmt = (
            select(User)
            .join(Follow, Follow.following_id == User.id)
            .where(and_(Follow.follower_id == uuid.UUID(user_id), User.is_active.is_(True)))
            .order_by(Follow.created_at.desc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())


    async def get_all_users(self) -> list[User]:
        stmt = select(User).order_by(User.handle)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_user_by_handle(self, handle: str) -> User | None:
        stmt = select(User).where(User.handle == handle.strip().lower())
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_user_model(self, user_id: uuid.UUID | str) -> User | None:
        uid = uuid.UUID(str(user_id)) if isinstance(user_id, str) else user_id
        stmt = select(User).where(User.id == uid)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def create_user(
        self,
        handle: str,
        display_name: str,
        password_hash: str,
        bio: str | None = None,
        avatar_small_url: str = "https://api.dicebear.com/7.x/avataaars/svg?seed=user",
        avatar_large_url: str = "https://api.dicebear.com/7.x/avataaars/svg?seed=user",
    ) -> User:
        user = User(
            handle=handle.strip().lower(),
            display_name=display_name.strip(),
            password_hash=password_hash,
            bio=bio.strip() if bio else None,
            avatar_small_url=avatar_small_url,
            avatar_large_url=avatar_large_url,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def create_session(self, user_id: uuid.UUID, token_hash: str, expires_at: datetime) -> UserSession:
        user_session = UserSession(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(user_session)
        await self.session.commit()
        await self.session.refresh(user_session)
        return user_session

    async def get_active_session(self, token_hash: str) -> UserSession | None:
        stmt = (
            select(UserSession)
            .options(selectinload(UserSession.user))
            .join(User, UserSession.user_id == User.id)
            .where(
                and_(
                    UserSession.token_hash == token_hash,
                    UserSession.revoked_at.is_(None),
                    UserSession.expires_at > func.now(),
                    User.is_active.is_(True),
                )
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def revoke_session(self, token_hash: str) -> bool:
        stmt = select(UserSession).where(
            and_(
                UserSession.token_hash == token_hash,
                UserSession.revoked_at.is_(None),
            )
        )
        res = await self.session.execute(stmt)
        sess = res.scalar_one_or_none()
        if not sess:
            return False
        sess.revoked_at = func.now()
        await self.session.commit()
        return True

    async def update_user_profile(
        self,
        user_id: uuid.UUID | str,
        display_name: str | None = None,
        bio: str | None = None,
        avatar_small_url: str | None = None,
        avatar_large_url: str | None = None,
    ) -> User | None:
        uid = uuid.UUID(str(user_id)) if isinstance(user_id, str) else user_id
        stmt = select(User).where(and_(User.id == uid, User.is_active.is_(True)))
        res = await self.session.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            return None
        if display_name is not None:
            user.display_name = display_name
        if bio is not None:
            user.bio = bio
        if avatar_small_url is not None:
            user.avatar_small_url = avatar_small_url
        if avatar_large_url is not None:
            user.avatar_large_url = avatar_large_url
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def deactivate_user(self, user_id: uuid.UUID | str) -> bool:
        uid = uuid.UUID(str(user_id)) if isinstance(user_id, str) else user_id
        stmt = select(User).where(User.id == uid)
        res = await self.session.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            return False
        user.is_active = False

        # Revoke all active sessions for this user
        sess_stmt = select(UserSession).where(
            and_(UserSession.user_id == uid, UserSession.revoked_at.is_(None))
        )
        sess_res = await self.session.execute(sess_stmt)
        for s in sess_res.scalars().all():
            s.revoked_at = func.now()
        await self.session.commit()
        return True

    async def get_notifications(self, user_id: str) -> list[Notification]:
        stmt = (
            select(Notification)
            .options(selectinload(Notification.actor))
            .where(Notification.recipient_id == uuid.UUID(user_id))
            .order_by(desc(Notification.created_at), desc(Notification.id))
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_unread_notification_count(self, user_id: str) -> int:
        stmt = select(func.count(Notification.id)).where(
            Notification.recipient_id == uuid.UUID(user_id),
            Notification.is_read.is_(False),
        )
        res = await self.session.execute(stmt)
        return res.scalar() or 0

    async def mark_notification_read(self, notification_id: str, user_id: str) -> Notification | str | None:
        stmt = (
            select(Notification)
            .options(selectinload(Notification.actor))
            .where(Notification.id == uuid.UUID(notification_id))
        )
        res = await self.session.execute(stmt)
        notif = res.scalar_one_or_none()
        if not notif:
            return None
        if str(notif.recipient_id) != user_id:
            return "FORBIDDEN"
        notif.is_read = True
        await self.session.commit()
        await self.session.refresh(notif)
        return notif

    async def mark_all_notifications_read(self, user_id: str) -> int:
        stmt = (
            update(Notification)
            .where(
                Notification.recipient_id == uuid.UUID(user_id),
                Notification.is_read.is_(False),
            )
            .values(is_read=True)
        )
        res = await self.session.execute(stmt)
        await self.session.commit()
        return res.rowcount or 0
