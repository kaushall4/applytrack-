"""Account connection endpoints: status, connect, disconnect."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...db import get_session
from ...gmail.auth import (
    connect_account,
    credential_status,
    disconnect_account,
    get_connected_address,
)
from ...models import SyncState
from ...schemas import AccountStatusOut, ConnectIn, MessageOut

router = APIRouter(prefix="/api/account", tags=["account"])


def _state(session: Session) -> SyncState:
    state = session.get(SyncState, 1)
    if state is None:
        state = SyncState(id=1)
        session.add(state)
    return state


@router.get("", response_model=AccountStatusOut)
def account_status(session: Session = Depends(get_session)) -> AccountStatusOut:
    """Connection state. Cheap: no Gmail API call once the address is known."""
    status = credential_status()
    state = session.get(SyncState, 1)
    address = state.email_address if state else None

    if status == "ok" and not address:
        # First run after connecting via an older version — look it up once.
        address = get_connected_address()
        if address:
            _state(session).email_address = address
            session.commit()

    return AccountStatusOut(
        connected=status in ("ok", "offline"),
        session_expired=status == "expired",
        # Kept after disconnect/expiry too, so the connect dialog can prefill it.
        email_address=address,
        last_synced_at=state.last_synced_at if state else None,
    )


@router.post("/connect", response_model=AccountStatusOut)
def connect(payload: ConnectIn, session: Session = Depends(get_session)) -> AccountStatusOut:
    """Launch the OAuth consent flow and verify the authorized account.

    This opens a browser on the machine running the backend. The account-intent
    check lives in :func:`connect_account`; a mismatch raises and is rendered as
    a 409 by the global handler. The address is remembered so a later reconnect
    is a single click.
    """
    address = connect_account(payload.email_address)
    state = _state(session)
    state.email_address = address
    session.commit()
    return AccountStatusOut(
        connected=True, email_address=address, last_synced_at=state.last_synced_at
    )


@router.post("/disconnect", response_model=MessageOut)
def disconnect() -> MessageOut:
    removed = disconnect_account()
    return MessageOut(
        message="Account disconnected." if removed else "No account was connected."
    )
