"""
The error envelope shape, matching the contract exactly:

{
  "error": {"code": "...", "message": "...", "details": [{"field": "...", "reason": "..."}]},
  "requestId": "..."
}
"""

from app.schemas.base import CamelModel


class ErrorDetail(CamelModel):
    field: str
    reason: str


class ErrorBody(CamelModel):
    code: str  # VALIDATION_ERROR | NOT_FOUND | CONFLICT | SERVICE_UNAVAILABLE | INTERNAL_ERROR
    message: str
    details: list[ErrorDetail] = []


class ErrorEnvelope(CamelModel):
    error: ErrorBody
    request_id: str