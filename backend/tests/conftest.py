"""
Shared pytest fixtures.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from app.main import app
from app.db.session import engine, async_session_factory
from app.db.models import User, Post, Like, Follow, UserSession
from app.fixtures.social_fixtures import ALL_POSTS, USERS

SEED_POST_IDS = [uuid.UUID(p["id"]) for p in ALL_POSTS]
SEED_USER_IDS = [uuid.UUID(u["id"]) for u in USERS]


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_client(client):
    reg = client.post("/auth/register", json={
        "handle": f"testuser_{uuid.uuid4().hex[:8]}",
        "displayName": "Test User",
        "password": "password123!",
    })
    token = reg.json()["token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture(autouse=True)
async def cleanup_database_and_engine():
    yield
    try:
        async with async_session_factory() as s:
            async with s.begin():
                await s.execute(delete(Like).where(~Like.post_id.in_(SEED_POST_IDS) | ~Like.user_id.in_(SEED_USER_IDS)))
                await s.execute(delete(Follow).where(~Follow.follower_id.in_(SEED_USER_IDS) | ~Follow.following_id.in_(SEED_USER_IDS)))
                await s.execute(delete(UserSession).where(~UserSession.user_id.in_(SEED_USER_IDS)))
                await s.execute(delete(Post).where(~Post.id.in_(SEED_POST_IDS)))
                await s.execute(delete(User).where(~User.id.in_(SEED_USER_IDS)))
    except Exception:
        pass
    await engine.dispose()