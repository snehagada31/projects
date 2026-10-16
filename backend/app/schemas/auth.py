from pydantic import Field, field_validator
from app.schemas.base import CamelModel
from app.schemas.user import Avatar


class RegisterRequest(CamelModel):
    handle: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    bio: str | None = Field(None, max_length=280)
    avatar_small_url: str | None = None
    avatar_large_url: str | None = None

    @field_validator("handle")
    @classmethod
    def normalize_handle(cls, v: str) -> str:
        trimmed = v.strip().lower()
        if not trimmed:
            raise ValueError("Handle cannot be empty")
        return trimmed

    @field_validator("display_name")
    @classmethod
    def clean_display_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Display name cannot be empty")
        return trimmed


class LoginRequest(CamelModel):
    handle: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("handle")
    @classmethod
    def normalize_handle(cls, v: str) -> str:
        return v.strip().lower()


class AuthUser(CamelModel):
    id: str
    handle: str
    display_name: str
    bio: str | None = None
    avatar: Avatar


class AuthResponse(CamelModel):
    token: str
    expires_at: str
    user: AuthUser


class AuthMessageResponse(CamelModel):
    message: str
