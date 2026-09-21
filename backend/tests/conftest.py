"""
Shared pytest fixtures.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import engine


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
async def cleanup_db_connections():
    yield
    await engine.dispose()