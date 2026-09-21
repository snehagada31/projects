"""
Shared query-param validation for every paginated route — cursor/limit
parsing, PLUS the checks FastAPI's typed Query() parameters don't do for
you automatically: rejecting duplicate params and unknown params
(including the legacy 'page' the brief explicitly calls out).

Why this can't just be Query(0, ge=0) on the route function: FastAPI's
normal typed params silently take one value if you pass ?cursor=a&cursor=b
in the URL, and silently IGNORE unknown params like ?page=2 entirely.
The contract wants both of those to be 400 errors — so this function
inspects the raw query string directly instead.
"""

from fastapi import Request
from app.common.errors import ValidationError
from app.common.cursors import decode_cursor

ALLOWED_FEED_PARAMS = {"cursor", "limit"}


def validate_pagination_params(request: Request, allowed: set[str] = ALLOWED_FEED_PARAMS):
    params = request.query_params

    for key in params.keys():
        if key not in allowed:
            # covers unknown params generally AND the specific legacy
            # "page" the brief calls out — page was never a supported
            # param, so it falls under this same check.
            raise ValidationError(f"unknown query parameter: {key}", field=key, reason="unknown_parameter")
        if len(params.getlist(key)) > 1:
            raise ValidationError(f"duplicate query parameter: {key}", field=key, reason="duplicate_parameter")

    limit_raw = params.get("limit", "10")
    try:
        limit = int(limit_raw)
    except ValueError:
        raise ValidationError("limit must be an integer", field="limit", reason="not_an_integer")

    if not (1 <= limit <= 50):
        raise ValidationError("limit must be an integer from 1 to 50", field="limit", reason="out_of_range")

    cursor_raw = params.get("cursor")
    cursor_tuple = decode_cursor(cursor_raw) if cursor_raw else None

    return cursor_tuple, limit