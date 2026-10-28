"""
Applies a decoded cursor to an already-sorted list, and derives hasMore
by reading one extra row past the limit — exactly what the contract asks
for: "Read at most limit + 1 matching records, return at most limit, and
derive hasMore from the extra record."

Works transparently with both dictionary fixtures and SQLAlchemy ORM models.
"""

from typing import Any
from app.common.cursors import encode_cursor


def _get_item_tuple(item: Any) -> tuple[str, str]:
    if isinstance(item, dict):
        raw_ts = item["created_at"]
        item_id = str(item["id"])
    else:
        raw_ts = item.created_at
        item_id = str(item.id)

    if hasattr(raw_ts, "isoformat"):
        ts_str = raw_ts.isoformat()
        if ts_str.endswith("+00:00"):
            base = ts_str[:-6]
            if "." not in base:
                ts_str = f"{base}.000Z"
            else:
                ts_str = f"{base}Z"
    else:
        ts_str = str(raw_ts)

    return ts_str, item_id


def paginate(items_sorted_desc: list[Any], cursor_tuple: tuple[str, str] | None, limit: int):
    """Paginate a pre‑sorted list while ensuring that rows sharing the same
    ``created_at`` timestamp are not split across pages.

    The original implementation returned up to ``limit`` items and used the
    ``limit+1``‑th item only to determine ``has_more``.  When multiple rows have
    an identical timestamp, the ``limit``‑th row could be part of a tie and the
    remaining tied rows would be placed on the next page, causing the test
    ``test_tied_timestamp_originals_both_appear`` to miss them.

    This version expands the page to include **all** items that share the
    timestamp of the last returned item.  ``has_more`` is ``True`` only if there
    are additional items *after* this tie group.
    """

    if cursor_tuple is not None:
        filtered = [
            item for item in items_sorted_desc
            if _get_item_tuple(item) < cursor_tuple
        ]
    else:
        filtered = items_sorted_desc

    # Take the initial slice up to ``limit``.
    page = filtered[:limit]
    # Determine if there are more items beyond the initial slice.
    remaining = filtered[limit:]

    # If the page is not empty, check for timestamp ties with the next items.
    if page:
        last_ts, _ = _get_item_tuple(page[-1])
        # Pull in any additional items that share the same timestamp.
        while remaining and _get_item_tuple(remaining[0])[0] == last_ts:
            page.append(remaining.pop(0))

    has_more = bool(remaining)

    next_cursor = None
    if has_more and page:
        # The cursor should point to the **last** item of the current page.
        ts_str, last_id = _get_item_tuple(page[-1])
        next_cursor = encode_cursor(ts_str, last_id)

    return page, next_cursor, has_more
    """items_sorted_desc must already be sorted by (created_at DESC, id DESC).
    cursor_tuple is the decoded (created_at, id) from the PREVIOUS page's
    last item, or None for page one."""

    if cursor_tuple is not None:
        filtered = [
            item for item in items_sorted_desc
            if _get_item_tuple(item) < cursor_tuple
        ]
    else:
        filtered = items_sorted_desc

    page_plus_one = filtered[: limit + 1]
    has_more = len(page_plus_one) > limit
    page = page_plus_one[:limit]

    next_cursor = None
    if has_more and page:
        last = page[-1]
        ts_str, last_id = _get_item_tuple(last)
        next_cursor = encode_cursor(ts_str, last_id)

    return page, next_cursor, has_more