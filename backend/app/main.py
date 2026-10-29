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
    # Stage C: nothing needed on startup (the engine connects lazily,
    # on first real query) — but shutdown MUST dispose the engine,
    # closing every pooled connection cleanly instead of leaving them
    # dangling when the process exits.
    yield
    from app.db.session import dispose_engine
    await dispose_engine()


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            settings.frontend_origin,
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
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