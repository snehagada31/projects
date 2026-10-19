"""
Post-related response shapes — the biggest schema in the contract.
Matches the brief's example JSON field-for-field.
"""

from pydantic import Field, field_validator, ConfigDict
from app.schemas.base import CamelModel
from app.schemas.user import AuthorSummary


class EditPostRequest(CamelModel):
    """
    Allowlist for editing post text by the author.
    Strictly forbids immutable fields (id, author_id, kind, created_at, reply_to_id, etc.)
    via extra="forbid".
    """
    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., min_length=1, max_length=280)

    @field_validator("text")
    @classmethod
    def clean_text(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Post text cannot be empty or whitespace only")
        return trimmed



class MediaItem(CamelModel):
    """Media embedded INSIDE a post response — not the same shape as the
    top-level /users/{id}/media list item (that one adds postId/createdAt,
    since it's not already nested under a post)."""
    id: str
    alt_text: str
    width: int
    height: int
    position: int
    small_url: str
    large_url: str


class ProfileMediaItem(CamelModel):
    """The shape used by GET /users/{id}/media — an Extension route for
    Stage A, built now since the shape is cheap to define alongside the
    rest, even though the route itself isn't wired up yet."""
    id: str
    post_id: str
    created_at: str
    position: int
    alt_text: str
    width: int
    height: int
    small_url: str
    large_url: str


class ReferencedPost(CamelModel):
    """Only present on a repost's detail response, so clients don't have
    to separately fetch the original post being reposted."""
    id: str
    text: str | None
    author: AuthorSummary


class PostItem(CamelModel):
    id: str
    kind: str  # "original" | "reply" | "repost"
    text: str | None
    created_at: str
    author: AuthorSummary
    media: list[MediaItem] = []
    like_count: int
    reply_count: int
    liked_by_viewer: bool
    reposted_by_viewer: bool = False
    retweet_count: int = 0
    reply_to_id: str | None = None
    repost_of_id: str | None = None


class PostDetailResponse(CamelModel):
    """GET /posts/{id} wraps the item under "item", per the brief.
    referenced_post is only populated for reposts."""
    item: PostItem
    referenced_post: ReferencedPost | None = None


class CreatePostRequest(CamelModel):
    kind: str
    text: str | None = None
    reply_to_id: str | None = None
    repost_of_id: str | None = None


class LikeResponse(CamelModel):
    post_id: str
    liked_by_viewer: bool
    like_count: int


class RepostResponse(CamelModel):
    post_id: str
    reposted_by_viewer: bool
    retweet_count: int

