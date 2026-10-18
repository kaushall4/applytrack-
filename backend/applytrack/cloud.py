"""Move ApplyTrack's data into a cloud Postgres database (e.g. Neon).

The phone app then runs from a free cloud host (see ``render.yaml``) that
shares this database, so it works while the laptop is off. The desktop app
switches to the same database, keeping one set of data and manual fixes.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from sqlalchemy import String, func, inspect, select, text

from .db import Base, make_engine, normalize_url

logger = logging.getLogger("applytrack.cloud")


class CloudSetupError(RuntimeError):
    pass


def copy_database(source_url: str, target_url: str, *, overwrite: bool = False) -> dict[str, int]:
    """Copy every ApplyTrack table from ``source_url`` to ``target_url``.

    Returns the number of rows copied per table. Refuses to touch a target that
    already holds emails unless ``overwrite`` is set.
    """
    from . import models  # noqa: F401 — register tables on the metadata

    source = make_engine(source_url)
    target = make_engine(target_url)
    Base.metadata.create_all(bind=target)
    tables = Base.metadata.sorted_tables

    with target.begin() as conn:
        existing = conn.execute(select(func.count()).select_from(models.Email.__table__)).scalar()
        if existing and not overwrite:
            raise CloudSetupError(
                f"The cloud database already contains {existing} email(s). "
                "Use --overwrite to replace them."
            )
        for table in reversed(tables):
            conn.execute(table.delete())

    copied: dict[str, int] = {}
    with source.connect() as src, target.begin() as dst:
        source_tables = set(inspect(source).get_table_names())
        for table in tables:
            if table.name not in source_tables:
                copied[table.name] = 0
                continue
            rows = [dict(r._mapping) for r in src.execute(select(table))]
            for row in rows:
                _fit_strings(table, row)
            if rows:
                dst.execute(table.insert(), rows)
            copied[table.name] = len(rows)
        if dst.dialect.name == "postgresql":
            _reset_sequences(dst, tables)
    return copied


def _fit_strings(table, row: dict) -> None:
    """SQLite ignores VARCHAR lengths, Postgres does not — trim overlong values."""
    for col in table.columns:
        value = row.get(col.name)
        if isinstance(col.type, String) and col.type.length and isinstance(value, str):
            row[col.name] = value[: col.type.length]


def _reset_sequences(conn, tables) -> None:
    """Explicit ids were inserted; move each id sequence past the copied rows."""
    for table in tables:
        pk = list(table.primary_key.columns)
        if len(pk) != 1 or not pk[0].autoincrement or pk[0].type.python_type is not int:
            continue
        conn.execute(
            text(
                f"SELECT setval(pg_get_serial_sequence('{table.name}', '{pk[0].name}'), "
                f"COALESCE((SELECT MAX({pk[0].name}) FROM {table.name}), 0) + 1, false)"
            )
        )


def store_shared_secrets(target_url: str, *, token_file: str, key: str) -> None:
    """Put the Gmail token and pairing key into the cloud database."""
    from sqlalchemy.orm import Session

    from .models import AppSecret
    from .secret_store import GMAIL_TOKEN, MOBILE_KEY

    target = make_engine(target_url)
    values = {MOBILE_KEY: key}
    token_path = Path(token_file)
    if token_path.exists():
        values[GMAIL_TOKEN] = token_path.read_text(encoding="utf-8")
    with Session(target) as session, session.begin():
        for name, value in values.items():
            row = session.get(AppSecret, name)
            if row is None:
                session.add(AppSecret(name=name, value=value))
            else:
                row.value = value


def set_env_values(values: dict[str, str], env_path: str = ".env") -> None:
    """Write/replace ``KEY=value`` lines in .env, keeping everything else."""
    path = Path(env_path)
    text_ = path.read_text(encoding="utf-8") if path.exists() else ""
    for name, value in values.items():
        line = f"{name}={value}"
        pattern = rf"^{re.escape(name)}=.*$"
        if re.search(pattern, text_, flags=re.MULTILINE):
            text_ = re.sub(pattern, lambda _m, line=line: line, text_, flags=re.MULTILINE)
        else:
            text_ = (text_.rstrip("\n") + "\n" if text_ else "") + line + "\n"
    path.write_text(text_, encoding="utf-8")


def check_postgres_url(url: str) -> str:
    url = url.strip().strip('"').strip("'")
    if not normalize_url(url).startswith("postgresql+psycopg://"):
        raise CloudSetupError("That does not look like a Postgres connection string (postgresql://…).")
    return url
