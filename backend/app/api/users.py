"""
GET /users/{id} — a user's profile, with postCount/followerCount/followingCount.
"""

import asyncio
import uuid
from fastapi import APIRouter, Depends, Query, Request

from app.repositories.social_repository import SocialRepository
from app.api.feed import get_social_repository
from app.schemas.user import (
    UserProfileResponse,
    UserProfileItem,
    Avatar,
    ProfileUpdateRequest,
    ExplainableUserSuggestion,
    UserSearchItem,
)
from app.schemas.pagination import PaginatedResponse
from app.schemas.auth import AuthMessageResponse
from app.common.errors import ValidationError, NotFoundError, AuthorizationError
from app.services.post_service import maybe_await
from app.services.auth_service import get_current_user, get_optional_current_user

from app.db.models import User
from app.config import settings
from app.common.fake_io import fake_io_operation


router = APIRouter()


def _validate_user_id(user_id: str) -> None:
    try:
        uuid.UUID(user_id)
    except ValueError:
        raise ValidationError("user id is not a valid UUID", field="id", reason="bad_uuid")


async def _build_user_profile_response(repo: SocialRepository, user: User | dict) -> UserProfileResponse:
    uid_str = str(user["id"] if isinstance(user, dict) else user.id)
    avatar_dict = user.get("avatar") or {} if isinstance(user, dict) else {}
    small_url = avatar_dict.get("small_url") if isinstance(user, dict) else getattr(user, "avatar_small_url", "")
    large_url = avatar_dict.get("large_url") if isinstance(user, dict) else getattr(user, "avatar_large_url", "")
    bio = user.get("bio") if isinstance(user, dict) else user.bio
    display_name = user["display_name"] if isinstance(user, dict) else user.display_name
    handle = user["handle"] if isinstance(user, dict) else user.handle

    post_count = await maybe_await(repo.get_post_count(uid_str))
    follower_count = await maybe_await(repo.get_follower_count(uid_str))
    following_count = await maybe_await(repo.get_following_count(uid_str))

    item = UserProfileItem(
        id=uid_str,
        handle=handle,
        display_name=display_name,
        bio=bio,
        avatar=Avatar(small_url=small_url, large_url=large_url),
        post_count=post_count,
        follower_count=follower_count,
        following_count=following_count,
    )
    return UserProfileResponse(item=item)


@router.patch("/users/me", response_model=UserProfileResponse)
async def update_my_profile(
    body: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    repo: SocialRepository = Depends(get_social_repository),
):
    updated = await maybe_await(
        repo.update_user_profile(
            user_id=current_user.id,
            display_name=body.display_name,
            bio=body.bio,
            avatar_small_url=body.avatar_small_url,
            avatar_large_url=body.avatar_large_url,
        )
    )
    if not updated:
        raise NotFoundError("User not found or deactivated")
    return await _build_user_profile_response(repo, updated)


@router.post("/users/me/deactivate", response_model=AuthMessageResponse)
async def deactivate_my_account(
    current_user: User = Depends(get_current_user),
    repo: SocialRepository = Depends(get_social_repository),
):
    await maybe_await(repo.deactivate_user(current_user.id))
    return AuthMessageResponse(message="Account successfully deactivated")


@router.patch("/users/{user_id}", response_model=UserProfileResponse)
async def update_user_profile_by_id(
    user_id: str,
    body: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    repo: SocialRepository = Depends(get_social_repository),
):
    _validate_user_id(user_id)
    if str(current_user.id) != user_id:
        raise AuthorizationError("Cannot update another user's profile")

    updated = await maybe_await(
        repo.update_user_profile(
            user_id=current_user.id,
            display_name=body.display_name,
            bio=body.bio,
            avatar_small_url=body.avatar_small_url,
            avatar_large_url=body.avatar_large_url,
        )
    )
    if not updated:
        raise NotFoundError("User not found or deactivated")
    return await _build_user_profile_response(repo, updated)


@router.get("/users/search", response_model=PaginatedResponse[UserSearchItem])
async def search_users(
    q: str = Query(..., min_length=1, max_length=100),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=50),
    current_user: User | None = Depends(get_optional_current_user),
    repo: SocialRepository = Depends(get_social_repository),
):
    viewer_id = str(current_user.id) if current_user else None
    if hasattr(repo, "search_users"):
        users, next_cursor, has_more = await maybe_await(repo.search_users(q, limit=limit, cursor=cursor))
    else:
        all_u = await maybe_await(repo.get_all_users())
        matched = [u for u in all_u if q.lower() in (u.get("handle") if isinstance(u, dict) else u.handle).lower()]
        users = matched[:limit]
        next_cursor = None
        has_more = len(matched) > limit

    items = []
    for u in users:
        u_id = str(u["id"] if isinstance(u, dict) else u.id)
        handle = u["handle"] if isinstance(u, dict) else u.handle
        display_name = u["display_name"] if isinstance(u, dict) else u.display_name
        bio = u.get("bio") if isinstance(u, dict) else u.bio
        avatar_dict = u.get("avatar") or {} if isinstance(u, dict) else {}
        small_url = avatar_dict.get("small_url") if isinstance(u, dict) else getattr(u, "avatar_small_url", "")
        large_url = avatar_dict.get("large_url") if isinstance(u, dict) else getattr(u, "avatar_large_url", "")

        f_cnt = await maybe_await(repo.get_follower_count(u_id))
        fg_cnt = await maybe_await(repo.get_following_count(u_id))
        is_following = await maybe_await(repo.is_following(viewer_id, u_id)) if viewer_id else False

        items.append(
            UserSearchItem(
                id=u_id,
                handle=handle,
                display_name=display_name,
                bio=bio,
                avatar=Avatar(small_url=small_url, large_url=large_url),
                follower_count=f_cnt,
                following_count=fg_cnt,
                following=is_following,
            )
        )

    return PaginatedResponse(items=items, next_cursor=next_cursor, has_more=has_more)


@router.get("/users/suggestions", response_model=list[ExplainableUserSuggestion])
async def get_user_suggestions(
    limit: int = Query(5, ge=1, le=20),
    current_user: User | None = Depends(get_optional_current_user),
    repo: SocialRepository = Depends(get_social_repository),
):
    viewer_id = str(current_user.id) if current_user else None
    if hasattr(repo, "get_explainable_suggestions"):
        raw_suggestions = await maybe_await(repo.get_explainable_suggestions(viewer_id=viewer_id, limit=limit))
    else:
        raw_suggestions = []

    results = []
    for s in raw_suggestions:
        u = s["user"]
        u_id = str(u["id"] if isinstance(u, dict) else u.id)
        handle = u["handle"] if isinstance(u, dict) else u.handle
        display_name = u["display_name"] if isinstance(u, dict) else u.display_name
        bio = u.get("bio") if isinstance(u, dict) else u.bio
        avatar_dict = u.get("avatar") or {} if isinstance(u, dict) else {}
        small_url = avatar_dict.get("small_url") if isinstance(u, dict) else getattr(u, "avatar_small_url", "")
        large_url = avatar_dict.get("large_url") if isinstance(u, dict) else getattr(u, "avatar_large_url", "")

        results.append(
            ExplainableUserSuggestion(
                id=u_id,
                handle=handle,
                display_name=display_name,
                bio=bio,
                avatar=Avatar(small_url=small_url, large_url=large_url),
                following=False,
                follower_count=s.get("follower_count", 0),
                reason=s.get("reason", "Popular in your network"),
            )
        )
    return results


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
async def list_users(
    q: str | None = None,
    current_user: User | None = Depends(get_optional_current_user),
    repo: SocialRepository = Depends(get_social_repository),
):
    users = await maybe_await(repo.get_all_users())
    results = []
    lowered = q.strip().lower() if q else None
    viewer_id = str(current_user.id) if current_user else None

    for u in users:
        u_id = str(u["id"] if isinstance(u, dict) else u.id)
        handle = u["handle"] if isinstance(u, dict) else u.handle
        display_name = u["display_name"] if isinstance(u, dict) else u.display_name
        bio = u.get("bio") if isinstance(u, dict) else u.bio

        if lowered:
            if lowered not in handle.lower() and lowered not in display_name.lower():
                continue
        elif viewer_id and u_id == viewer_id:
            # Skip self for suggestions when not searching
            continue

        avatar_dict = u.get("avatar") or {} if isinstance(u, dict) else {}
        small_url = avatar_dict.get("small_url") if isinstance(u, dict) else getattr(u, "avatar_small_url", "")
        large_url = avatar_dict.get("large_url") if isinstance(u, dict) else getattr(u, "avatar_large_url", "")
        is_following = await maybe_await(repo.is_following(viewer_id, u_id)) if viewer_id else False
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
async def follow_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    repo: SocialRepository = Depends(get_social_repository),
):
    _validate_user_id(user_id)
    if user_id == str(current_user.id):
        raise ValidationError("users cannot follow themselves", field="id", reason="self_follow", status_code=422)
    target = await maybe_await(repo.get_user(user_id))
    if not target:
        raise NotFoundError("user not found")

    await maybe_await(repo.add_follow(str(current_user.id), user_id))
    follower_count = await maybe_await(repo.get_follower_count(user_id))
    return FollowResponse(user_id=user_id, following=True, follower_count=follower_count)


@router.delete("/users/{user_id}/follow", response_model=FollowResponse)
async def unfollow_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    repo: SocialRepository = Depends(get_social_repository),
):
    _validate_user_id(user_id)
    await maybe_await(repo.remove_follow(str(current_user.id), user_id))
    follower_count = await maybe_await(repo.get_follower_count(user_id))
    return FollowResponse(user_id=user_id, following=False, follower_count=follower_count)


@router.get("/users/{user_id}/followers", response_model=list[UserFollowSuggestion])
async def list_followers(
    user_id: str,
    current_user: User | None = Depends(get_optional_current_user),
    repo: SocialRepository = Depends(get_social_repository),
):
    _validate_user_id(user_id)
    target = await maybe_await(repo.get_user(user_id))
    if not target:
        raise NotFoundError("user not found")

    followers = await maybe_await(repo.get_followers(user_id))
    viewer_id = str(current_user.id) if current_user else None
    results = []
    for u in followers:
        u_id = str(u["id"] if isinstance(u, dict) else u.id)
        handle = u["handle"] if isinstance(u, dict) else u.handle
        display_name = u["display_name"] if isinstance(u, dict) else u.display_name
        bio = u.get("bio") if isinstance(u, dict) else u.bio
        avatar_dict = u.get("avatar") or {} if isinstance(u, dict) else {}
        small_url = avatar_dict.get("small_url") if isinstance(u, dict) else getattr(u, "avatar_small_url", "")
        large_url = avatar_dict.get("large_url") if isinstance(u, dict) else getattr(u, "avatar_large_url", "")
        is_following = await maybe_await(repo.is_following(viewer_id, u_id)) if viewer_id else False
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


@router.get("/users/{user_id}/following", response_model=list[UserFollowSuggestion])
async def list_following(
    user_id: str,
    current_user: User | None = Depends(get_optional_current_user),
    repo: SocialRepository = Depends(get_social_repository),
):
    _validate_user_id(user_id)
    target = await maybe_await(repo.get_user(user_id))
    if not target:
        raise NotFoundError("user not found")

    following = await maybe_await(repo.get_following(user_id))
    viewer_id = str(current_user.id) if current_user else None
    results = []
    for u in following:
        u_id = str(u["id"] if isinstance(u, dict) else u.id)
        handle = u["handle"] if isinstance(u, dict) else u.handle
        display_name = u["display_name"] if isinstance(u, dict) else u.display_name
        bio = u.get("bio") if isinstance(u, dict) else u.bio
        avatar_dict = u.get("avatar") or {} if isinstance(u, dict) else {}
        small_url = avatar_dict.get("small_url") if isinstance(u, dict) else getattr(u, "avatar_small_url", "")
        large_url = avatar_dict.get("large_url") if isinstance(u, dict) else getattr(u, "avatar_large_url", "")
        is_following = await maybe_await(repo.is_following(viewer_id, u_id)) if viewer_id else False
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