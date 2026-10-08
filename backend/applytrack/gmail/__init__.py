"""Gmail integration: read-only OAuth, account verification, and sync."""

from .auth import (
    AccountMismatchError,
    GmailAuthError,
    SessionExpiredError,
    connect_account,
    credential_status,
    disconnect_account,
    get_connected_address,
    get_gmail_service,
    is_connected,
)

__all__ = [
    "AccountMismatchError",
    "GmailAuthError",
    "SessionExpiredError",
    "connect_account",
    "credential_status",
    "disconnect_account",
    "get_connected_address",
    "get_gmail_service",
    "is_connected",
]
