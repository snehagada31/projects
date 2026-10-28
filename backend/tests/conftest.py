"""
Shared pytest fixtures.
"""

import uuid
import asyncio
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from app.main import app
from app.db.session import engine, async_session_factory
from app.db.models import User, Post, Like, Follow, UserSession, Notification
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
