"""
Authentication service and FastAPI dependency for Stage 1 (PY-P0-01).
Enforces:
- Constant-time verification to prevent user enumeration
- Bounded session lifetime (24 hours)
- Instant token revocation on logout
- Strict bearer token extraction via Depends(get_current_user)
"""

from datetime import datetime, timezone, timedelta
from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.db.models import User
from app.repositories.postgres_repository import PostgresSocialRepository
from app.common.security import (
    hash_password,
    verify_password,
    generate_session_token,
    hash_session_token,
)
from app.common.errors import (
    AuthenticationError,
    ConflictError,
    ValidationError,
)
from app.schemas.auth import RegisterRequest, LoginRequest, AuthResponse, AuthUser
from app.schemas.user import Avatar

# 24-hour session lifetime per decision record
SESSION_TTL_HOURS = 24

bearer_scheme = HTTPBearer(auto_error=False)


def _user_to_auth_user(user: User) -> AuthUser:
    return AuthUser(
        id=str(user.id),
        handle=user.handle,
        display_name=user.display_name,
        bio=user.bio,
        avatar=Avatar(
            small_url=user.avatar_small_url,
            large_url=user.avatar_large_url,
        ),
    )


async def register_account(
    repo: PostgresSocialRepository,
    req: RegisterRequest,
) -> AuthResponse:
    # Check for existing handle before hashing to fail fast on validation
    existing = await repo.get_user_by_handle(req.handle)
    if existing:
        raise ConflictError(f"Handle @{req.handle} is already taken")

    pwd_hash = await hash_password(req.password)
    default_avatar = f"https://api.dicebear.com/7.x/avataaars/svg?seed={req.handle}"
    small_url = req.avatar_small_url or default_avatar
    large_url = req.avatar_large_url or default_avatar

    try:
        user = await repo.create_user(
            handle=req.handle,
            display_name=req.display_name,
            password_hash=pwd_hash,
            bio=req.bio,
            avatar_small_url=small_url,
            avatar_large_url=large_url,
        )
    except IntegrityError:
        # Handles concurrent race where two users register the same handle at the same millisecond
        raise ConflictError(f"Handle @{req.handle} is already taken")

    raw_token = generate_session_token()
    token_hash = hash_session_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=SESSION_TTL_HOURS)

    await repo.create_session(user.id, token_hash, expires_at)

    return AuthResponse(
        token=raw_token,
        expires_at=expires_at.isoformat(),
        user=_user_to_auth_user(user),
    )


async def authenticate_account(
    repo: PostgresSocialRepository,
    req: LoginRequest,
) -> AuthResponse:
    user = await repo.get_user_by_handle(req.handle)
    
    # Constant-time verify: runs dummy check if user is None to block timing enumeration
    is_valid = await verify_password(req.password, user.password_hash if user else None)
    if not user or not is_valid:
        raise AuthenticationError("Invalid handle or password")

    raw_token = generate_session_token()
    token_hash = hash_session_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=SESSION_TTL_HOURS)

    await repo.create_session(user.id, token_hash, expires_at)

    return AuthResponse(
        token=raw_token,
        expires_at=expires_at.isoformat(),
        user=_user_to_auth_user(user),
    )


async def revoke_current_session(
    repo: PostgresSocialRepository,
    token: str,
) -> None:
    token_hash = hash_session_token(token)
    revoked = await repo.revoke_session(token_hash)
    if not revoked:
        raise AuthenticationError("Invalid or already revoked session")


async def get_current_user(
    auth: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """
    FastAPI dependency that extracts the verified actor from Bearer auth header.
    Guarantees that protected actions derive actor ONLY from verified credentials.
    """
    if not auth or not auth.credentials:
        raise AuthenticationError("Authentication credentials were not provided")

    token_hash = hash_session_token(auth.credentials)
    repo = PostgresSocialRepository(db)
    session = await repo.get_active_session(token_hash)

    if not session or not session.user:
        raise AuthenticationError("Invalid or expired session token")

    return session.user


async def get_optional_current_user(
    auth: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> User | None:
    """
    FastAPI dependency for public read surfaces (e.g. GET /feed) where
    viewer state is optional: returns User if authenticated, else None.
    """
    if not auth or not auth.credentials:
        return None

    token_hash = hash_session_token(auth.credentials)
    repo = PostgresSocialRepository(db)
    session = await repo.get_active_session(token_hash)
    return session.user if session else None
