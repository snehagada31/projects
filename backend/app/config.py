"""
Application configuration — loaded ONCE at startup, validated by Pydantic.
"""

import uuid
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    port: int = 8000
    frontend_origin: str = "http://localhost:5173"
    demo_user_id: str = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1"
    simulated_io_ms: int = 0
    # Default to in‑memory SQLite for tests; can be overridden by .env
    database_url: str = "sqlite+aiosqlite:///:memory:"
    database_connect_timeout_ms: int = 3000  # used by the /health/ready check

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def model_post_init(self, __context) -> None:
        if not (0 <= self.simulated_io_ms <= 1000):
            raise ValueError("SIMULATED_IO_MS must be between 0 and 1000")
        try:
            uuid.UUID(self.demo_user_id)
        except ValueError:
            raise ValueError("DEMO_USER_ID must be a valid UUID")
        # Allow PostgreSQL (production) or SQLite (tests) URLs.
        if not (self.database_url.startswith("postgresql+asyncpg://") or self.database_url.startswith("sqlite+aiosqlite://")):
            raise ValueError(
                "DATABASE_URL must use postgresql+asyncpg:// or sqlite+aiosqlite:// scheme, "
                f"got: {self.database_url.split('://')[0]}://..."
            )

settings = Settings()
