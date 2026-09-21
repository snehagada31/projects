"""
Application configuration — loaded ONCE at startup, validated by Pydantic.

Stage C change from Stage A: database_url is now REQUIRED, not optional
— Stage A explicitly didn't need a database yet; Stage C's entire point
is persistence, so a missing DATABASE_URL should fail loudly at startup,
not silently limp along without a database.
"""

import uuid
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    port: int = 8000
    frontend_origin: str = "http://localhost:5173"
    demo_user_id: str = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1"
    simulated_io_ms: int = 0
    database_url: str  # REQUIRED now — no default, missing = startup failure
    database_connect_timeout_ms: int = 3000  # used by the /health/ready check

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def model_post_init(self, __context) -> None:
        if not (0 <= self.simulated_io_ms <= 1000):
            raise ValueError("SIMULATED_IO_MS must be between 0 and 1000")
        try:
            uuid.UUID(self.demo_user_id)
        except ValueError:
            raise ValueError("DEMO_USER_ID must be a valid UUID")
        if not self.database_url.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "DATABASE_URL must use the postgresql+asyncpg:// scheme for the async engine, "
                f"got: {self.database_url.split('://')[0]}://..."
            )


settings = Settings()