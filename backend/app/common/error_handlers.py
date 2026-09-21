"""
Maps every kind of failure — our own raised errors, FastAPI's default
validation errors, and genuinely unexpected crashes — into ONE consistent
envelope shape. Without this file, a bad query param would return
FastAPI's default (different shape, always 422) instead of the
contract's {"error": {...}, "requestId": ...} with the correct 400/422
split.
"""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse

from app.common.errors import AppError
from app.schemas.errors import ErrorEnvelope, ErrorBody, ErrorDetail


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def _respond(request: Request, status_code: int, code: str, message: str, details: list[dict] | None = None):
    envelope = ErrorEnvelope(
        error=ErrorBody(
            code=code,
            message=message,
            details=[ErrorDetail(field=d.get("field", ""), reason=d.get("reason", "")) for d in (details or [])],
        ),
        request_id=_request_id(request),
    )
    return JSONResponse(
        status_code=status_code,
        content=envelope.model_dump(by_alias=True),
        headers={"X-Request-Id": _request_id(request)},
    )


async def app_error_handler(request: Request, exc: AppError):
    """Handles every error WE raise on purpose (NotFoundError, ValidationError, etc.)"""
    return _respond(request, exc.status_code, exc.code, exc.message, exc.details)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handles FastAPI's AUTOMATIC validation failures — e.g. someone
    passes limit=abc (not an integer). FastAPI's default here is 422 with
    a different JSON shape; the contract wants 400 for query/path
    problems, 422 reserved for body/domain failures. This function is
    what makes that split actually happen, per PY-S05's explicit
    requirement: 'no framework-default shape leaks.'
    """
    is_body_error = False
    details = []
    for err in exc.errors():
        loc = err.get("loc", [])
        field = str(loc[-1]) if loc else "unknown"
        details.append({"field": field, "reason": err.get("type", "invalid")})
        if loc and loc[0] == "body":
            is_body_error = True

    status_code = 422 if is_body_error else 400
    return _respond(request, status_code, "VALIDATION_ERROR", "request validation failed", details)


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handles FastAPI's default 404 (unmatched route) and any explicit
    HTTPException raised anywhere in the app, mapping the status code to
    the matching envelope code."""
    code_by_status = {404: "NOT_FOUND", 409: "CONFLICT", 503: "SERVICE_UNAVAILABLE"}
    code = code_by_status.get(exc.status_code, "INTERNAL_ERROR")
    message = str(exc.detail) if exc.detail else "error"
    return _respond(request, exc.status_code, code, message)


async def unhandled_exception_handler(request: Request, exc: Exception):
    """Last resort — a genuinely unexpected crash. Message is deliberately
    generic: never leak a stack trace, exception message, or internal
    detail to the client, per 'Dependency override raises' -> 'no raw
    traceback or environment values' in the acceptance tests."""
    return _respond(request, 500, "INTERNAL_ERROR", "an unexpected error occurred")