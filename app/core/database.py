"""Synchronous SQLite engine, session factory and table-creation helper.

Sync (not aiosqlite/async) on purpose: aiosqlite pulls in greenlet, which has
no prebuilt wheel for Python 3.14 and fails to compile without C++ Build Tools.
FastAPI runs sync `Depends()` in a threadpool, so there is no event-loop block.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel

from app.core.config import settings

# echo SQL statements everywhere except production (easier debugging in dev).
engine = create_engine(
    settings.DATABASE_URL,
    echo=not settings.is_production,
    connect_args={"check_same_thread": False},
)

# class_=Session -> SQLModel's Session, so `session.exec(select(...))` works.
SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a `Session` and always closes it."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_db_and_tables() -> None:
    """Create all tables registered on SQLModel.metadata. Call once on startup."""
    # Importing the models package registers every table on the metadata.
    from app import models  # noqa: F401

    # Standalone ambassador entities (not in app/models/__init__.py) — import
    # explicitly so SQLModel.metadata sees their tables before create_all.
    from app.models.ambassador import Ambassador  # noqa: F401
    from app.models.ambassador_application import (  # noqa: F401
        AmbassadorApplication,
    )

    SQLModel.metadata.create_all(engine)
