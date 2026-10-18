"""Database engine and session management.

Uses SQLAlchemy 2.0 style. SQLite is the default; any `DATABASE_URL` that
SQLAlchemy understands (e.g. Postgres) is a drop-in replacement with no code
changes — the only SQLite-specific tweak (`check_same_thread`) is applied
conditionally.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def normalize_url(url: str) -> str:
    """Accept the plain ``postgres(ql)://`` URLs hosts hand out (Neon, Render)
    and route them to the psycopg 3 driver."""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


def make_engine(url: str):
    url = normalize_url(url)
    connect_args = {}
    kwargs = {}
    if url.startswith("sqlite"):
        # SQLite + FastAPI's threadpool need this; harmless otherwise.
        connect_args["check_same_thread"] = False
    else:
        # Serverless Postgres (e.g. Neon) drops idle connections; check first.
        kwargs["pool_pre_ping"] = True
    return create_engine(url, connect_args=connect_args, future=True, **kwargs)


def _make_engine():
    return make_engine(get_settings().database_url)


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def init_db() -> None:
    """Create tables if they do not yet exist."""
    # Import models so they register on the metadata before create_all.
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a scoped session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Context manager for use outside the request lifecycle (CLI, sync)."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
