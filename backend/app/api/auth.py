"""
Authentication endpoints for Stage 1 (PY-P0-01):
- POST /auth/register: Registers new member and returns active session
- POST /auth/login: Authenticates credentials and returns active session
- POST /auth/logout: Revokes current session token
- GET /auth/me: Returns verified current authenticated user profile
"""

import uuid
from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.db.models import User
from app.repositories.postgres_repository import PostgresSocialRepository
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    AuthResponse,
    AuthUser,
    AuthMessageResponse,
    SessionItem,
    SessionsResponse,
)
from app.services.auth_service import (
    register_account,
    authenticate_account,
    revoke_current_session,
    get_current_user,
    bearer_scheme,
    _user_to_auth_user,
)
from app.common.security import hash_session_token
from app.common.errors import AuthenticationError, NotFoundError, ValidationError

router = APIRouter(prefix="/auth", tags=["auth"])


def get_social_repo(db: AsyncSession = Depends(get_db_session)) -> PostgresSocialRepository:
    return PostgresSocialRepository(db)


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new member account",
)
async def register(
    req: RegisterRequest,
    repo: PostgresSocialRepository = Depends(get_social_repo),
):
    return await register_account(repo, req)


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Sign in with handle and password",
)
async def login(
    req: LoginRequest,
    repo: PostgresSocialRepository = Depends(get_social_repo),
):
    return await authenticate_account(repo, req)


@router.post(
    "/logout",
    response_model=AuthMessageResponse,
    summary="Sign out and invalidate current session token",
)
async def logout(
    auth: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    repo: PostgresSocialRepository = Depends(get_social_repo),
):
    if not auth or not auth.credentials:
        raise AuthenticationError("Authentication credentials were not provided")
    await revoke_current_session(repo, auth.credentials)
    return AuthMessageResponse(message="Successfully signed out")


@router.get(
    "/me",
    response_model=AuthUser,
    summary="Get authenticated member profile",
)
async def me(
    current_user: User = Depends(get_current_user),
):
    return _user_to_auth_user(current_user)


@router.get(
    "/sessions",
    response_model=SessionsResponse,
    summary="List all active login sessions for the authenticated user",
)
async def list_sessions(
    auth: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    current_user: User = Depends(get_current_user),
    repo: PostgresSocialRepository = Depends(get_social_repo),
):
    current_hash = hash_session_token(auth.credentials) if auth and auth.credentials else ""
    sessions = await repo.get_user_active_sessions(current_user.id)
    items = [
        SessionItem(
            id=str(s.id),
            created_at=s.created_at.isoformat(),
            expires_at=s.expires_at.isoformat(),
            is_current=(s.token_hash == current_hash),
        )
        for s in sessions
    ]
    return SessionsResponse(sessions=items)


@router.delete(
    "/sessions/{session_id}",
    response_model=AuthMessageResponse,
    summary="Revoke a specific session by ID",
)
async def revoke_session_by_id(
    session_id: str,
    current_user: User = Depends(get_current_user),
    repo: PostgresSocialRepository = Depends(get_social_repo),
):
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise ValidationError("Invalid session id", field="session_id", reason="invalid_uuid", status_code=422)

    revoked = await repo.revoke_session_by_id(current_user.id, sid)
    if not revoked:
        raise NotFoundError("Session not found or already revoked")
    return AuthMessageResponse(message="Session dismissed successfully")


@router.post(
    "/sessions/revoke-others",
    response_model=AuthMessageResponse,
    summary="Revoke all other active sessions except the current one",
)
async def revoke_other_sessions(
    auth: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    current_user: User = Depends(get_current_user),
    repo: PostgresSocialRepository = Depends(get_social_repo),
):
    if not auth or not auth.credentials:
        raise AuthenticationError("Authentication credentials were not provided")
    current_hash = hash_session_token(auth.credentials)
    count = await repo.revoke_other_sessions(current_user.id, current_hash)
    return AuthMessageResponse(message=f"Revoked {count} other active session(s)")
