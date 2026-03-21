from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import get_settings

settings = get_settings()

# Create the SQLAlchemy engine using the configured database URL.
# connect_args is only needed for SQLite (disables same-thread check).
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=settings.db_echo,
)

# Session factory — use as a context manager or dependency in FastAPI
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


def get_db():
    """
    FastAPI dependency that yields a database session and ensures
    it is closed after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Create all tables defined on Base.metadata.
    Call this on application startup when not using Alembic migrations.
    """
    # Import models here so their table definitions are registered on Base
    from models import todo  # noqa: F401
    Base.metadata.create_all(bind=engine)
