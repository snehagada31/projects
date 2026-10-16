"""
Authentication endpoints for Stage 1 (PY-P0-01):
- POST /auth/register: Registers new member and returns active session
- POST /auth/login: Authenticates credentials and returns active session
- POST /auth/logout: Revokes current session token
- GET /auth/me: Returns verified current authenticated user profile
"""

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
)
from app.services.auth_service import (
    register_account,
    authenticate_account,
    revoke_current_session,
    get_current_user,
    bearer_scheme,
    _user_to_auth_user,
)
from app.common.errors import AuthenticationError

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
