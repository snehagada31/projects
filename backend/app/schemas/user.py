"""
User-related response shapes, matching the brief exactly:
- AuthorSummary: the small author block embedded inside every post
- UserProfile: the fuller shape returned by GET /users/{id}
"""

from pydantic import Field, field_validator, ConfigDict
from app.schemas.base import CamelModel


class ProfileUpdateRequest(CamelModel):
    """
    Allowlist for updating member profile.
    Strictly forbids immutable fields (id, handle, created_at, counts)
    or unknown properties via extra="forbid".
    """
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(None, min_length=1, max_length=100)
    bio: str | None = Field(None, max_length=280)
    avatar_small_url: str | None = None
    avatar_large_url: str | None = None

    @field_validator("display_name")
    @classmethod
    def clean_display_name(cls, v: str | None) -> str | None:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Display name cannot be empty")
            return trimmed
        return v



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


class ExplainableUserSuggestion(CamelModel):
    id: str
    handle: str
    display_name: str
    bio: str | None = None
    avatar: Avatar
    following: bool = False
    follower_count: int = 0
    reason: str = "Popular in your network"


class UserSearchItem(CamelModel):
    id: str
    handle: str
    display_name: str
    bio: str | None = None
    avatar: Avatar
    follower_count: int = 0
    following_count: int = 0
    following: bool = False
