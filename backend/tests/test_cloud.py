"""Cloud copy: URL handling, shared secrets, data copy and cloud-mode guard."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from applytrack import cloud, mobile
from applytrack.api.app import create_app
from applytrack.config import get_settings
from applytrack.db import make_engine, normalize_url
from applytrack.gmail import auth
from applytrack.models import Application, AppSecret, Email
from applytrack.secret_store import GMAIL_TOKEN, MOBILE_KEY, get_secret, set_secret


def test_normalize_url_routes_postgres_to_psycopg():
    assert normalize_url("postgres://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert normalize_url("postgresql://u:p@h/db?sslmode=require").startswith("postgresql+psycopg://")
    assert normalize_url("sqlite:///x.db") == "sqlite:///x.db"


def test_check_postgres_url_rejects_other_strings():
    with pytest.raises(cloud.CloudSetupError):
        cloud.check_postgres_url("https://example.com")
    assert cloud.check_postgres_url(' "postgresql://u:p@h/db" ') == "postgresql://u:p@h/db"


def test_cloud_mode_trusts_no_client(monkeypatch):
    monkeypatch.setattr(get_settings(), "cloud_mode", True)
    assert not mobile.is_local_client("127.0.0.1")
    resp = TestClient(create_app(), client=("127.0.0.1", 50000)).get("/api/applications")
    assert resp.status_code == 401


def test_token_is_restored_from_database(tmp_path, monkeypatch):
    token_file = tmp_path / "token.json"
    monkeypatch.setattr(get_settings(), "google_token_file", str(token_file))
    set_secret(GMAIL_TOKEN, '{"token": "x"}')
    assert auth._restore_token_from_db(str(token_file))
    assert token_file.read_text(encoding="utf-8") == '{"token": "x"}'


def test_disconnect_also_forgets_database_token(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "google_token_file", str(tmp_path / "token.json"))
    set_secret(GMAIL_TOKEN, "{}")
    assert auth.disconnect_account() is True
    assert get_secret(GMAIL_TOKEN) is None


def _seed(url: str) -> None:
    engine = make_engine(url)
    from applytrack.db import Base

    Base.metadata.create_all(bind=engine)
    now = datetime.now(UTC)
    with Session(engine) as s, s.begin():
        app = Application(company="Acme", role="Analyst", group_key="acme|analyst",
                          current_status="applied", first_applied_at=now, last_event_at=now)
        s.add(app)
        s.flush()
        s.add(Email(gmail_id="g1", thread_id="t1", application_id=app.id, subject="Hi",
                    received_at=now, intent="application_received"))


def test_copy_database_moves_rows_and_secrets(tmp_path):
    source = f"sqlite:///{(tmp_path / 'local.db').as_posix()}"
    target = f"sqlite:///{(tmp_path / 'cloud.db').as_posix()}"
    _seed(source)
    token = tmp_path / "token.json"
    token.write_text('{"refresh_token": "r"}', encoding="utf-8")

    copied = cloud.copy_database(source, target)
    cloud.store_shared_secrets(target, token_file=str(token), key="k3y")

    assert copied["emails"] == 1 and copied["applications"] == 1
    with Session(make_engine(target)) as s:
        assert s.scalar(select(func.count()).select_from(Email)) == 1
        assert s.get(AppSecret, MOBILE_KEY).value == "k3y"
        assert "refresh_token" in s.get(AppSecret, GMAIL_TOKEN).value

    # A filled cloud database is never overwritten by accident.
    with pytest.raises(cloud.CloudSetupError):
        cloud.copy_database(source, target)
    assert cloud.copy_database(source, target, overwrite=True)["emails"] == 1


def test_set_env_values_replaces_and_appends(tmp_path):
    env = tmp_path / ".env"
    env.write_text("A=1\nDATABASE_URL=sqlite:///./x.db\n", encoding="utf-8")
    cloud.set_env_values({"DATABASE_URL": "postgresql://u:p@h/db", "CLOUD_URL": "https://x"}, str(env))
    text = env.read_text(encoding="utf-8")
    assert "A=1" in text
    assert "DATABASE_URL=postgresql://u:p@h/db" in text and "sqlite" not in text
    assert "CLOUD_URL=https://x" in text


def test_mobile_status_points_qr_at_cloud(monkeypatch):
    monkeypatch.setattr(get_settings(), "cloud_url", "https://applytrack.example")
    data = TestClient(create_app(), client=("127.0.0.1", 50000)).get("/api/mobile").json()
    assert data["enabled"] and data["cloud"]
    assert data["url"].startswith("https://applytrack.example/?key=")
