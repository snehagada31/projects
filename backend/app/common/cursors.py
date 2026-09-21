"""
Cursor encode/decode — the contract's exact format:
  base64url({"v": 1, "createdAt": "...", "id": "..."})

Why base64url instead of a raw integer offset: the contract says a
cursor is "an opaque client continuation token, not an authorization
credential" — the client shouldn't be able to read or construct one by
hand, and OFFSET-based paging breaks when rows are inserted between
requests (items shift, causing skips/duplicates). Encoding the last
seen (createdAt, id) pair means each page says "give me everything
older than THIS exact point," which stays correct even if new rows
appear.
"""

import base64
import json
import uuid

from app.common.errors import ValidationError

MAX_CURSOR_LENGTH = 1024


def encode_cursor(created_at: str, post_id: str) -> str:
    payload = {"v": 1, "createdAt": created_at, "id": post_id}
    raw = json.dumps(payload).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def decode_cursor(cursor: str) -> tuple[str, str]:
    """Returns (created_at, id) if valid. Raises ValidationError otherwise."""

    if len(cursor) > MAX_CURSOR_LENGTH:
        raise ValidationError("cursor exceeds maximum length", field="cursor", reason="too_long")

    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("ascii"))
    except Exception:
        raise ValidationError("cursor is not valid base64url", field="cursor", reason="bad_encoding")

    try:
        payload = json.loads(raw)
    except Exception:
        raise ValidationError("cursor does not decode to valid JSON", field="cursor", reason="bad_json")

    if not isinstance(payload, dict):
        raise ValidationError("cursor payload must be an object", field="cursor", reason="bad_shape")

    if payload.get("v") != 1:
        raise ValidationError("unsupported cursor version", field="cursor", reason="bad_version")

    created_at = payload.get("createdAt")
    post_id = payload.get("id")

    if not isinstance(created_at, str) or not created_at:
        raise ValidationError("cursor missing valid createdAt", field="cursor", reason="bad_timestamp")

    if not isinstance(post_id, str):
        raise ValidationError("cursor missing valid id", field="cursor", reason="bad_id")

    try:
        uuid.UUID(post_id)
    except ValueError:
        raise ValidationError("cursor id is not a valid UUID", field="cursor", reason="bad_id")

    return created_at, post_id