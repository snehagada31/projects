"""
GET /users/{id} — a user's profile, with postCount/followerCount/followingCount.
"""

import asyncio
import uuid
from fastapi import APIRouter, Depends

from app.repositories.social_repository import SocialRepository
from app.api.feed import get_social_repository
from app.schemas.user import UserProfileResponse, UserProfileItem, Avatar
from app.common.errors import ValidationError, NotFoundError
from app.services.post_service import maybe_await
from app.config import settings
from app.common.fake_io import fake_io_operation

router = APIRouter()


def _validate_user_id(user_id: str) -> None:
    try:
        uuid.UUID(user_id)
    except ValueError:
        raise ValidationError("user id is not a valid UUID", field="id", reason="bad_uuid")


@router.get("/users/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str,
    repo: SocialRepository = Depends(get_social_repository),
):
    _validate_user_id(user_id)

    async with fake_io_operation("get_user_profile"):
        if settings.simulated_io_ms > 0:
            await asyncio.sleep(settings.simulated_io_ms / 1000)

    user = await maybe_await(repo.get_user(user_id))
    if user is None:
        raise NotFoundError("user not found")

    avatar_dict = user.get("avatar") or {} if isinstance(user, dict) else {}
    small_url = avatar_dict.get("small_url") if isinstance(user, dict) else getattr(user, "avatar_small_url", "")
    large_url = avatar_dict.get("large_url") if isinstance(user, dict) else getattr(user, "avatar_large_url", "")

    post_count = await maybe_await(repo.get_post_count(user_id))
    follower_count = await maybe_await(repo.get_follower_count(user_id))
    following_count = await maybe_await(repo.get_following_count(user_id))

    item = UserProfileItem(
        id=str(user["id"] if isinstance(user, dict) else user.id),
        handle=user["handle"] if isinstance(user, dict) else user.handle,
        display_name=user["display_name"] if isinstance(user, dict) else user.display_name,
        bio=user.get("bio") if isinstance(user, dict) else user.bio,
        avatar=Avatar(small_url=small_url, large_url=large_url),
        post_count=post_count,
        follower_count=follower_count,
        following_count=following_count,
    )

    return UserProfileResponse(item=item)


from fastapi import Request
from app.schemas.post import ProfileMediaItem
from app.schemas.pagination import PaginatedResponse
from app.common.query_validation import validate_pagination_params
from app.common.pagination import paginate


@router.get("/users/{user_id}/media", response_model=PaginatedResponse[ProfileMediaItem])
async def get_user_media(
    user_id: str,
    request: Request,
    repo: SocialRepository = Depends(get_social_repository),
):
    _validate_user_id(user_id)
    user = await maybe_await(repo.get_user(user_id))
    if user is None:
        raise NotFoundError("user not found")

    cursor_tuple, limit = validate_pagination_params(request)
    media_list = await maybe_await(repo.get_user_media(user_id))
    page, next_cursor, has_more = paginate(media_list, cursor_tuple, limit)

    items = [
        ProfileMediaItem(
            id=str(m["id"] if isinstance(m, dict) else m.id),
            post_id=str(m["post_id"] if isinstance(m, dict) else m.post_id),
            created_at=(
                m["created_at"]
                if isinstance(m, dict)
                else (m.created_at.isoformat() if hasattr(m.created_at, "isoformat") else str(m.created_at))
            ),
            position=m["position"] if isinstance(m, dict) else m.position,
            alt_text=m["alt_text"] if isinstance(m, dict) else m.alt_text,
            width=m["width"] if isinstance(m, dict) else m.width,
            height=m["height"] if isinstance(m, dict) else m.height,
            small_url=m["small_url"] if isinstance(m, dict) else m.small_url,
            large_url=m["large_url"] if isinstance(m, dict) else m.large_url,
        )
        for m in page
    ]

    return PaginatedResponse(items=items, next_cursor=next_cursor, has_more=has_more)


from app.schemas.user import FollowResponse, UserFollowSuggestion


@router.get("/users", response_model=list[UserFollowSuggestion])
async def list_users(q: str | None = None, repo: SocialRepository = Depends(get_social_repository)):
    users = await maybe_await(repo.get_all_users())
    results = []
    lowered = q.strip().lower() if q else None
    for u in users:
        u_id = str(u["id"] if isinstance(u, dict) else u.id)
        handle = u["handle"] if isinstance(u, dict) else u.handle
        display_name = u["display_name"] if isinstance(u, dict) else u.display_name
        bio = u.get("bio") if isinstance(u, dict) else u.bio

        if lowered:
            if lowered not in handle.lower() and lowered not in display_name.lower():
                continue
        elif u_id == settings.demo_user_id:
            # Skip self for suggestions when not searching
            continue

        avatar_dict = u.get("avatar") or {} if isinstance(u, dict) else {}
        small_url = avatar_dict.get("small_url") if isinstance(u, dict) else getattr(u, "avatar_small_url", "")
        large_url = avatar_dict.get("large_url") if isinstance(u, dict) else getattr(u, "avatar_large_url", "")
        is_following = await maybe_await(repo.is_following(settings.demo_user_id, u_id))
        results.append(
            UserFollowSuggestion(
                id=u_id,
                handle=handle,
                display_name=display_name,
                bio=bio,
                avatar=Avatar(small_url=small_url, large_url=large_url),
                following=is_following,
            )
        )
    return results


@router.put("/users/{user_id}/follow", response_model=FollowResponse)
async def follow_user(user_id: str, repo: SocialRepository = Depends(get_social_repository)):
    _validate_user_id(user_id)
    if user_id == settings.demo_user_id:
        raise ValidationError("users cannot follow themselves", field="id", reason="self_follow", status_code=422)
    target = await maybe_await(repo.get_user(user_id))
    if not target:
        raise NotFoundError("user not found")

    await maybe_await(repo.add_follow(settings.demo_user_id, user_id))
    follower_count = await maybe_await(repo.get_follower_count(user_id))
    return FollowResponse(user_id=user_id, following=True, follower_count=follower_count)


@router.delete("/users/{user_id}/follow", response_model=FollowResponse)
async def unfollow_user(user_id: str, repo: SocialRepository = Depends(get_social_repository)):
    _validate_user_id(user_id)
    await maybe_await(repo.remove_follow(settings.demo_user_id, user_id))
    follower_count = await maybe_await(repo.get_follower_count(user_id))
    return FollowResponse(user_id=user_id, following=False, follower_count=follower_count)