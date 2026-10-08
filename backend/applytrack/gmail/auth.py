"""Read-only Gmail OAuth, with explicit account-intent verification.

Important security note (mirrored in the README): typing an email address in
the UI only declares *intent*. Access is granted solely by whoever completes
Google's consent screen. After OAuth we therefore call the Gmail profile
endpoint and verify the authenticated address matches the intended one — if it
doesn't, we discard the token and refuse to connect.
"""

from __future__ import annotations

import logging
import os
from typing import Literal

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from ..config import get_settings

logger = logging.getLogger("applytrack.gmail")

# Read-only — ApplyTrack never modifies or deletes mail.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# "ok": usable token · "missing": never connected / disconnected ·
# "expired": Google rejected the refresh token (revoked, or the 7-day limit for
# OAuth apps in "Testing" status) · "offline": couldn't reach Google to refresh.
CredentialStatus = Literal["ok", "missing", "expired", "offline"]


class GmailAuthError(RuntimeError):
    """Raised for any OAuth / credential problem."""


class SessionExpiredError(GmailAuthError):
    """The stored Gmail authorisation is no longer accepted — reconnect needed."""

    def __init__(self) -> None:
        super().__init__(
            "Your Gmail connection has expired. Please reconnect your account."
        )


class AccountMismatchError(GmailAuthError):
    """Raised when the authorized account differs from the intended address."""

    def __init__(self, intended: str, authorized: str) -> None:
        self.intended = intended
        self.authorized = authorized
        super().__init__(
            f"You authorized {authorized} but asked to track {intended} — "
            f"please reconnect with the right account."
        )


def _token_path() -> str:
    return get_settings().google_token_file


def _credentials_path() -> str:
    return get_settings().google_credentials_file


def _load_credentials() -> tuple[CredentialStatus, Credentials | None]:
    """Load the cached token, refreshing (and re-saving) it when needed."""
    path = _token_path()
    if not os.path.exists(path):
        return "missing", None
    try:
        creds = Credentials.from_authorized_user_file(path, SCOPES)
    except (ValueError, OSError) as exc:
        logger.warning("Could not load cached token: %s", exc)
        return "missing", None

    if creds.valid:
        return "ok", creds
    if not creds.refresh_token:
        return "expired", None
    try:
        creds.refresh(Request())
    except RefreshError as exc:
        # invalid_grant: revoked, or the 7-day refresh-token lifetime of OAuth
        # apps still in "Testing" status. Only a new consent fixes this.
        logger.warning("Gmail session expired (%s); reconnect required.", exc)
        return "expired", None
    except Exception as exc:  # noqa: BLE001 — network etc.; the token may still be fine
        logger.warning("Could not refresh Gmail token right now: %s", type(exc).__name__)
        return "offline", None
    _save_credentials(creds)
    return "ok", creds


def credential_status() -> CredentialStatus:
    """Connection state without calling the Gmail API (cheap; safe to poll)."""
    return _load_credentials()[0]


def _load_cached_credentials() -> Credentials | None:
    return _load_credentials()[1]


def _save_credentials(creds: Credentials) -> None:
    with open(_token_path(), "w", encoding="utf-8") as fh:
        fh.write(creds.to_json())


def _profile_address(creds: Credentials) -> str:
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    profile = service.users().getProfile(userId="me").execute()
    return profile.get("emailAddress", "")


def is_connected() -> bool:
    return credential_status() in ("ok", "offline")


def get_connected_address() -> str | None:
    creds = _load_cached_credentials()
    if not creds:
        return None
    try:
        return _profile_address(creds)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not read connected profile: %s", exc)
        return None


def get_gmail_service():
    """Return an authorized Gmail API client, or raise if not connected."""
    status, creds = _load_credentials()
    if status == "expired":
        raise SessionExpiredError()
    if status == "offline":
        raise GmailAuthError("Could not reach Google. Check your internet connection.")
    if not creds:
        raise GmailAuthError("No Gmail account connected. Run `applytrack connect` first.")
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def connect_account(intended_address: str, *, open_browser: bool = True) -> str:
    """Run the OAuth consent flow and verify the authorized address.

    Returns the verified, connected email address. Raises
    :class:`AccountMismatchError` (and discards the token) if the authorized
    account is not the one the user intended to track.
    """
    intended_address = intended_address.strip().lower()
    cred_path = _credentials_path()
    if not os.path.exists(cred_path):
        raise GmailAuthError(
            f"OAuth client file '{cred_path}' not found. Download it from the "
            f"Google Cloud Console (see README) and place it here."
        )

    flow = InstalledAppFlow.from_client_secrets_file(cred_path, SCOPES)
    # Runs a short-lived local server to catch the OAuth redirect. When
    # ``open_browser`` is False (e.g. headless), it prints the URL to visit
    # instead of launching a browser. ``access_type=offline`` + ``prompt=consent``
    # guarantee a refresh token (so the user stays signed in); ``login_hint``
    # pre-selects the intended Google account to make reconnecting one click.
    extra = {"login_hint": intended_address} if intended_address else {}
    creds = flow.run_local_server(
        port=0,
        prompt="consent",
        access_type="offline",
        open_browser=open_browser,
        timeout_seconds=300,
        **extra,
    )

    authorized = _profile_address(creds).strip().lower()
    if intended_address and authorized != intended_address:
        # Do NOT persist a token for the wrong account.
        raise AccountMismatchError(intended=intended_address, authorized=authorized)

    _save_credentials(creds)
    logger.info("Connected Gmail account %s", authorized)
    return authorized


def disconnect_account() -> bool:
    """Delete the cached token. Returns True if a token was removed."""
    path = _token_path()
    if os.path.exists(path):
        os.remove(path)
        logger.info("Disconnected Gmail account (token removed).")
        return True
    return False
