"""
Application factory pattern.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

import os
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api import health, feed, posts, users, auth, notifications
from app.common.request_id import RequestIdMiddleware
from app.common.errors import AppError
from app.common.error_handlers import (
    app_error_handler,
    validation_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create tables and seed data if using PostgreSQL on Render/production
    try:
        from app.db.session import engine
        from app.db.models import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        # Idempotent seed
        from app.db.seed import seed_database
        await seed_database()
    except Exception as e:
        print("Database startup auto-migration/seed note:", e)

    yield
    from app.db.session import dispose_engine
    await dispose_engine()


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    if settings.frontend_origin:
        for orig in settings.frontend_origin.split(","):
            cleaned = orig.strip().rstrip("/")
            if cleaned and cleaned not in allowed_origins:
                allowed_origins.append(cleaned)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_origin_regex=r"https:\/\/.*\.vercel\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id"],
    )
    app.add_middleware(RequestIdMiddleware)

    # Order matters: FastAPI checks handlers most-specific-first, so
    # AppError (our own errors) is registered separately from the
    # generic Exception catch-all — both can coexist correctly.
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(feed.router)
    app.include_router(posts.router)
    app.include_router(users.router)
    app.include_router(notifications.router)

    uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
    os.makedirs(uploads_dir, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

    return app


app = create_app()