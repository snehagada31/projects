"""
GET /feed — reverse-chronological originals only, per the brief.
Uses PostgresSocialRepository when database is active, or FixtureSocialRepository.
"""

import asyncio
import inspect
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.db.models import User
from app.repositories.social_repository import SocialRepository, FixtureSocialRepository
from app.repositories.postgres_repository import PostgresSocialRepository
from app.common.query_validation import validate_pagination_params
from app.common.pagination import paginate
from app.services.post_service import build_post_item, maybe_await
from app.services.auth_service import get_optional_current_user
from app.schemas.post import PostItem
from app.schemas.pagination import PaginatedResponse
from app.config import settings
from app.common.fake_io import fake_io_operation

router = APIRouter()


def get_social_repository(db: AsyncSession = Depends(get_db_session)) -> SocialRepository:
    return PostgresSocialRepository(db)


@router.get("/feed", response_model=PaginatedResponse[PostItem])
async def get_feed(
    request: Request,
    current_user: User | None = Depends(get_optional_current_user),
    repo: SocialRepository = Depends(get_social_repository),
):
    cursor_tuple, limit = validate_pagination_params(request)

    async with fake_io_operation("get_feed"):
        if settings.simulated_io_ms > 0:
            await asyncio.sleep(settings.simulated_io_ms / 1000)

    viewer_id = str(current_user.id) if current_user else None

    # Personalized feed if authenticated: shows followed authors + self
    if viewer_id and hasattr(repo, "get_personalized_feed"):
        posts = await maybe_await(repo.get_personalized_feed(viewer_id))
    else:
        # Public feed for anonymous visitor or fixture repo
        posts = await maybe_await(repo.get_originals_sorted())

    page, next_cursor, has_more = paginate(posts, cursor_tuple, limit)

    items = [await build_post_item(repo, post, viewer_id=viewer_id) for post in page]

    return PaginatedResponse(items=items, next_cursor=next_cursor, has_more=has_more)