import os
from functools import lru_cache


class Settings:
    """Application configuration loaded from environment variables."""

    # Database URL — defaults to local SQLite for development
    database_url: str = os.getenv(
        "DATABASE_URL", "sqlite:///./todos.db"
    )

    # SQLite needs this flag; other backends (Postgres, MySQL) don't
    @property
    def connect_args(self) -> dict:
        if self.database_url.startswith("sqlite"):
            return {"check_same_thread": False}
        return {}

    # Optional: allow overriding echo/debug mode
    db_echo: bool = os.getenv("DB_ECHO", "false").lower() == "true"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()
