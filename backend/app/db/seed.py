"""
Explicit seed command: seeds PostgreSQL with the exact reviewed fixture data.
Can be executed via: python -m app.db.seed
"""

import asyncio
import uuid
from datetime import datetime
from sqlalchemy import text as sql_text
from sqlalchemy.dialects.postgresql import insert
from app.db.session import engine, async_session_factory
from app.db.models import User, Post, PostMedia, Like, Follow
from app.fixtures.social_fixtures import USERS, ALL_POSTS, MEDIA, LIKES, FOLLOWS


def parse_timestamp(ts_str: str) -> datetime:
    # "2026-09-01T10:00:00.000Z" -> datetime
    cleaned = ts_str.replace("Z", "+00:00")
    return datetime.fromisoformat(cleaned)


async def seed_database():
    print("Beginning idempotent database seed...")
    async with async_session_factory() as session:
        async with session.begin():
            # 1. Users
            for u in USERS:
                stmt = insert(User).values(
                    id=uuid.UUID(u["id"]),
                    handle=u["handle"],
                    display_name=u["display_name"],
                    bio=u.get("bio"),
                    avatar_small_url=u["avatar"]["small_url"],
                    avatar_large_url=u["avatar"]["large_url"],
                ).on_conflict_do_nothing(index_elements=["id"])
                await session.execute(stmt)

            # 2. Posts (originals first, then replies/reposts)
            for p in ALL_POSTS:
                stmt = insert(Post).values(
                    id=uuid.UUID(p["id"]),
                    author_id=uuid.UUID(p["author_id"]),
                    kind=p["kind"],
                    text=p.get("text"),
                    created_at=parse_timestamp(p["created_at"]),
                    reply_to_id=uuid.UUID(p["reply_to_id"]) if p.get("reply_to_id") else None,
                    repost_of_id=uuid.UUID(p["repost_of_id"]) if p.get("repost_of_id") else None,
                ).on_conflict_do_nothing(index_elements=["id"])
                await session.execute(stmt)

            # 3. PostMedia
            for m in MEDIA:
                stmt = insert(PostMedia).values(
                    id=uuid.UUID(m["id"]),
                    post_id=uuid.UUID(m["post_id"]),
                    alt_text=m["alt_text"],
                    width=m["width"],
                    height=m["height"],
                    position=m["position"],
                    small_url=m["small_url"],
                    large_url=m["large_url"],
                ).on_conflict_do_nothing(index_elements=["id"])
                await session.execute(stmt)

            # 4. Likes
            for l in LIKES:
                stmt = insert(Like).values(
                    user_id=uuid.UUID(l["user_id"]),
                    post_id=uuid.UUID(l["post_id"]),
                ).on_conflict_do_nothing(index_elements=["user_id", "post_id"])
                await session.execute(stmt)

            # 5. Follows
            for f in FOLLOWS:
                stmt = insert(Follow).values(
                    follower_id=uuid.UUID(f["follower_id"]),
                    following_id=uuid.UUID(f["following_id"]),
                ).on_conflict_do_nothing(index_elements=["follower_id", "following_id"])
                await session.execute(stmt)

        # Verification query per seed-manifest
        u_count = await session.scalar(sql_text("SELECT count(*) FROM users"))
        p_count = await session.scalar(sql_text("SELECT count(*) FROM posts"))
        m_count = await session.scalar(sql_text("SELECT count(*) FROM post_media"))
        l_count = await session.scalar(sql_text("SELECT count(*) FROM likes"))
        f_count = await session.scalar(sql_text("SELECT count(*) FROM follows"))

        print(f"Seed complete:")
        print(f"  - Users: {u_count} (expected 6)")
        print(f"  - Posts: {p_count} (expected 46: 30 originals, 12 replies, 4 reposts)")
        print(f"  - Media: {m_count} (expected 10)")
        print(f"  - Likes: {l_count} (expected 15)")
        print(f"  - Follows: {f_count} (expected 8)")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_database())
