"""
Custom exception hierarchy — one class per error code in the contract.
Routes raise these directly (e.g. raise NotFoundError("post not found")),
and a FastAPI exception handler (error_handlers.py) catches them and
builds the exact envelope shape.
"""


class AppError(Exception):
    """Base class. Never raised directly — always one of the subclasses below."""
    code = "INTERNAL_ERROR"
    status_code = 500

    def __init__(self, message: str, details: list[dict] | None = None, status_code: int | None = None):
        self.message = message
        self.details = details or []
        if status_code is not None:
            # allows ValidationError to be used for BOTH 400 (query/path)
            # and 422 (body/domain) — same error CODE, different HTTP
            # status, exactly as the contract specifies.
            self.status_code = status_code
        super().__init__(message)


class ValidationError(AppError):
    code = "VALIDATION_ERROR"
    status_code = 400  # override to 422 when raised for body/domain failures

    def __init__(self, message: str, field: str | None = None, reason: str | None = None, status_code: int | None = None):
        details = [{"field": field, "reason": reason}] if field else []
        super().__init__(message, details=details, status_code=status_code)


class NotFoundError(AppError):
    code = "NOT_FOUND"
    status_code = 404


class ConflictError(AppError):
    code = "CONFLICT"
    status_code = 409


class ServiceUnavailableError(AppError):
    code = "SERVICE_UNAVAILABLE"
    status_code = 503