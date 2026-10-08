"""Sync endpoints: trigger a sync and read sync metadata."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...db import get_session
from ...gmail.sync import sync_mailbox
from ...schemas import SyncResultOut

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.post("", response_model=SyncResultOut)
def trigger_sync(
    full: bool = Query(False, description="Force a full re-sync instead of incremental."),
    session: Session = Depends(get_session),
) -> SyncResultOut:
    result = sync_mailbox(session, full=full)
    return SyncResultOut(
        new_emails=result.new_emails,
        classified=result.classified,
        applications=result.applications,
        message=result.message,
    )
