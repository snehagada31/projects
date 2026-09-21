"""
Tests transaction rollback and atomicity (PRD 03 Deliverable 5 & PRD 05 C3).
Demonstrates:
- Performing a valid insert then forcing a constraint violation in the same transaction.
- Verifying the entire transaction rolls back and neither partial effect survives.
- Verifying duplicate like rejection by primary key constraint.
"""

import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.db.session import async_session_factory
from app.db.models import Post, Like
from app.fixtures.social_fixtures import USERS, ORIGINALS


@pytest.mark.asyncio
async def test_transaction_rollback_and_duplicate_integrity():
    """
    Demonstrates:
    1. A valid insert rolled back completely when a subsequent operation fails in the transaction.
    2. A duplicate like violating composite primary key raises IntegrityError and rolls back.
    """
    user_id = uuid.UUID(USERS[0]["id"])
    bogus_post_id = uuid.UUID("99999999-9999-4999-8999-999999999999")
    probe_post_id = uuid.uuid4()

    # Part 1: Rollback atomicity test
    async with async_session_factory() as session:
        try:
            async with session.begin():
                valid_post = Post(
                    id=probe_post_id,
                    author_id=user_id,
                    kind="original",
                    text="Transaction rollback probe post",
                )
                session.add(valid_post)
                await session.flush()

                # Invalid foreign-key write: references non-existent post
                invalid_like = Like(
                    user_id=user_id,
                    post_id=bogus_post_id,
                )
                session.add(invalid_like)
                await session.flush()
        except IntegrityError:
            pass

    # Verify that probe_post_id was rolled back and does not exist in the DB
    async with async_session_factory() as verify_session:
        stmt = select(Post).where(Post.id == probe_post_id)
        res = await verify_session.execute(stmt)
        surviving_post = res.scalar_one_or_none()
        assert surviving_post is None, "Partial insert survived rollback! Transaction was not atomic."

    # Part 2: Duplicate like integrity test
    post_id = uuid.UUID(ORIGINALS[0]["id"])
    async with async_session_factory() as setup_session:
        async with setup_session.begin():
            existing = await setup_session.get(Like, (user_id, post_id))
            if not existing:
                setup_session.add(Like(user_id=user_id, post_id=post_id))

    raised = False
    async with async_session_factory() as session2:
        try:
            async with session2.begin():
                dup_like = Like(user_id=user_id, post_id=post_id)
                session2.add(dup_like)
                await session2.flush()
        except IntegrityError:
            raised = True

    assert raised, "Expected IntegrityError on duplicate like, but none was raised"

