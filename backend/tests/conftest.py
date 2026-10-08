"""Pytest fixtures. Forces an isolated SQLite DB and no API key (heuristic path).

The env vars are set *before* any ``applytrack`` import so the engine and
settings singletons pick them up.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

# Isolated, ephemeral DB + offline classifier for the whole test session.
_TMP_DB = Path(tempfile.gettempdir()) / "applytrack_test.db"
if _TMP_DB.exists():
    _TMP_DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB.as_posix()}"
os.environ.pop("ANTHROPIC_API_KEY", None)
os.environ["ANTHROPIC_API_KEY"] = ""

# Point Gmail credential/token paths at non-existent temp files so account
# status is deterministically "disconnected" regardless of any real token.json
# in the working directory.
_TMP = Path(tempfile.gettempdir())
os.environ["GOOGLE_TOKEN_FILE"] = str(_TMP / "applytrack_test_token.json")
os.environ["GOOGLE_CREDENTIALS_FILE"] = str(_TMP / "applytrack_test_credentials.json")

import pytest  # noqa: E402

from applytrack.db import Base, SessionLocal, engine  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_schema():
    """Recreate the schema around every test for full isolation."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def session():
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()
