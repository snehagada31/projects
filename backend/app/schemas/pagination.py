"""
Generic paginated-list response — shared by /feed, /posts/{id}/replies,
/users/{id}/media and /search/posts, since they all return the exact
same wrapper shape: {"items": [...], "nextCursor": ..., "hasMore": ...}

Generic[T] means this one class works for a list of PostItem, a list of
ProfileMediaItem, or anything else — you write the pagination wrapper
logic ONCE instead of once per endpoint.
"""

from typing import Generic, TypeVar
from app.schemas.base import CamelModel

T = TypeVar("T")


class PaginatedResponse(CamelModel, Generic[T]):
    items: list[T]
    next_cursor: str | None
    has_more: bool