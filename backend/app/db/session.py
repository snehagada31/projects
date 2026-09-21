"""
One engine, one session factory, for the whole app's lifetime.

Why NOT create an engine per request: an engine owns a CONNECTION POOL
— creating a new one per request would open/close raw TCP connections
to Postgres constantly, which is slow and can exhaust the database's
max connection limit under load. One engine, reused everywhere, is what
lets connection pooling actually work.

Why NOT share one mutable AsyncSession across concurrent requests:
a session tracks pending changes and identity-maps loaded objects — if
two concurrent requests touched the same session, their changes could
interleave and corrupt each other. Each request/task gets ITS OWN
session, created fresh from the shared session factory.
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings

# echo=False in normal use; flip to True temporarily to see every SQL
# statement SQLAlchemy actually sends — useful for verifying there's no
# hidden N+1 query loop.
engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)

# expire_on_commit=False: without this, every attribute access on an
# object AFTER commit() triggers a fresh DB query to re-fetch it (lazy
# refresh) — which silently breaks the moment the session is closed
# (the classic "DetachedInstanceError"). Since this app converts
# SQLAlchemy objects to Pydantic schemas BEFORE the session closes
# (never lazy-loading after), this is safe — documented here as a
# deliberate choice, not a default left unexamined.
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session() -> AsyncSession:
    """FastAPI dependency — creates a fresh session per request, closes
    it when the request ends (the `async with` block), whether it
    succeeded or raised."""
    async with async_session_factory() as session:
        yield session


async def dispose_engine():
    """Called once, at application shutdown (in main.py's lifespan) —
    closes every pooled connection cleanly instead of leaving them
    dangling when the process exits."""
    await engine.dispose()