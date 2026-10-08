"""Application endpoints: summary stats, filterable list, and detail."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...db import get_session
from ...models import Application
from ...schemas import ApplicationDetailOut, ApplicationOut, StatsOut
from ...status import Status

router = APIRouter(prefix="/api/applications", tags=["applications"])

_SORTABLE = {
    "company": Application.company,
    "role": Application.role,
    "status": Application.current_status,
    "first_applied_at": Application.first_applied_at,
    "last_event_at": Application.last_event_at,
}

# Statuses that count as "awaiting a response from the company".
_AWAITING = {Status.APPLICATION_SENT.value, Status.APPLICATION_RECEIVED.value, Status.GHOSTED.value}
_INTERVIEWING = {Status.INTERVIEW_INVITE.value, Status.NEXT_ROUND.value}


@router.get("/stats", response_model=StatsOut)
def stats(session: Session = Depends(get_session)) -> StatsOut:
    rows = session.execute(
        select(Application.current_status, func.count(Application.id)).group_by(
            Application.current_status
        )
    ).all()
    by_status = {status: count for status, count in rows}

    def total(statuses: set[str]) -> int:
        return sum(by_status.get(s, 0) for s in statuses)

    return StatsOut(
        total_applied=sum(by_status.values()),
        awaiting_response=total(_AWAITING),
        interviews=total(_INTERVIEWING),
        offers=by_status.get(Status.OFFER.value, 0),
        rejections=by_status.get(Status.REJECTION.value, 0),
        ghosted=by_status.get(Status.GHOSTED.value, 0),
    )


@router.get("", response_model=list[ApplicationOut])
def list_applications(
    status: str | None = Query(None, description="Filter by current status."),
    language: str | None = Query(None, description="Filter by application language (de/en)."),
    sort: str = Query("last_event_at", description="Sort field."),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    session: Session = Depends(get_session),
) -> list[Application]:
    stmt = select(Application)
    if status:
        stmt = stmt.where(Application.current_status == status)
    if language:
        stmt = stmt.where(Application.language == language)

    column = _SORTABLE.get(sort, Application.last_event_at)
    stmt = stmt.order_by(column.desc() if order == "desc" else column.asc())

    return list(session.execute(stmt).scalars().all())


@router.get("/{application_id}", response_model=ApplicationDetailOut)
def application_detail(
    application_id: int, session: Session = Depends(get_session)
) -> Application:
    app = session.get(Application, application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found.")
    return app
