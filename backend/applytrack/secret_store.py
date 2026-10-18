"""Read/write the shared key/value secrets (see :class:`models.AppSecret`)."""

from __future__ import annotations

import logging

from sqlalchemy.exc import SQLAlchemyError

from .db import session_scope
from .models import AppSecret

logger = logging.getLogger("applytrack.secrets")

GMAIL_TOKEN = "gmail_token"
MOBILE_KEY = "mobile_key"
PAIR_CODE = "pair_code"


def get_secret(name: str) -> str | None:
    try:
        with session_scope() as session:
            row = session.get(AppSecret, name)
            return row.value if row else None
    except SQLAlchemyError as exc:  # e.g. table not created yet
        logger.warning("Could not read secret %s: %s", name, type(exc).__name__)
        return None


def set_secret(name: str, value: str) -> None:
    with session_scope() as session:
        row = session.get(AppSecret, name)
        if row is None:
            session.add(AppSecret(name=name, value=value))
        else:
            row.value = value


def delete_secret(name: str) -> None:
    try:
        with session_scope() as session:
            row = session.get(AppSecret, name)
            if row is not None:
                session.delete(row)
    except SQLAlchemyError as exc:
        logger.warning("Could not delete secret %s: %s", name, type(exc).__name__)
