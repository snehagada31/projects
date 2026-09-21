"""
User-related response shapes, matching the brief exactly:
- AuthorSummary: the small author block embedded inside every post
- UserProfile: the fuller shape returned by GET /users/{id}
"""

from app.schemas.base import CamelModel


class Avatar(CamelModel):
    small_url: str
    large_url: str


class AuthorSummary(CamelModel):
    """Embedded inside a post — NOT the full profile, just enough to
    render an author row (matches the brief's "author" block exactly)."""
    id: str
    handle: str
    display_name: str
    avatar: Avatar


class UserProfileItem(CamelModel):
    id: str
    handle: str
    display_name: str
    bio: str | None = None
    avatar: Avatar
    post_count: int   # originals only, per the brief
    follower_count: int
    following_count: int


class UserProfileResponse(CamelModel):
    """GET /users/{id} wraps the profile under "item", per the brief."""
    item: UserProfileItem


class FollowResponse(CamelModel):
    user_id: str
    following: bool
    follower_count: int


class UserFollowSuggestion(CamelModel):
    id: str
    handle: str
    display_name: str
    bio: str | None = None
    avatar: Avatar
    following: bool = False