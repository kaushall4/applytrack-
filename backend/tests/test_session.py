"""Gmail session handling: expired tokens are detected and surfaced cleanly."""

from __future__ import annotations

import json
import os

import pytest
from fastapi.testclient import TestClient
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials

from applytrack.api.app import create_app
from applytrack.config import get_settings
from applytrack.db import SessionLocal
from applytrack.gmail import auth
from applytrack.models import SyncState


@pytest.fixture
def expired_token(monkeypatch):
    """A cached token whose refresh Google rejects (invalid_grant)."""
    path = get_settings().google_token_file
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(
            {
                "token": "stale",
                "refresh_token": "revoked",
                "client_id": "id",
                "client_secret": "secret",
                "token_uri": "https://oauth2.googleapis.com/token",
                "expiry": "2020-01-01T00:00:00Z",
                "scopes": auth.SCOPES,
            },
            fh,
        )

    def _refuse(self, request):
        raise RefreshError("invalid_grant: Token has been expired or revoked.")

    monkeypatch.setattr(Credentials, "refresh", _refuse)
    yield
    os.remove(path)


@pytest.fixture
def remembered_account():
    s = SessionLocal()
    s.add(SyncState(id=1, email_address="me@example.com"))
    s.commit()
    s.close()


def test_missing_token_is_missing():
    assert auth.credential_status() == "missing"


def test_rejected_refresh_is_expired(expired_token):
    assert auth.credential_status() == "expired"
    with pytest.raises(auth.SessionExpiredError):
        auth.get_gmail_service()


def test_account_status_reports_expired_session(expired_token, remembered_account):
    data = TestClient(create_app()).get("/api/account").json()
    assert data["connected"] is False
    assert data["session_expired"] is True
    # The address is kept so the UI can offer a one-click reconnect.
    assert data["email_address"] == "me@example.com"


def test_sync_with_expired_session_returns_401(expired_token):
    resp = TestClient(create_app()).post("/api/sync")
    assert resp.status_code == 401
    assert resp.json()["code"] == "session_expired"
