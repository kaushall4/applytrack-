"""Application endpoints: summary stats, filterable list, and detail."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ...db import get_session
from ...models import INTERVIEW_STAGE_INTENTS, Application, Email
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

# Statuses that count as "awaiting a response from the company" (still within the
# ghost threshold — older silent ones are counted as ghosted instead).
_AWAITING = {Status.APPLICATION_SENT.value, Status.APPLICATION_RECEIVED.value}


def _interviewed_app_ids():
    """Applications that ever reached an interview / further round / offer —
    a past interview still counts after a rejection."""
    effective_intent = func.coalesce(Email.manual_override, Email.intent)
    return select(Email.application_id).where(
        Email.application_id.is_not(None),
        effective_intent.in_(INTERVIEW_STAGE_INTENTS),
    )


def _next_round_app_ids():
    """Applications that ever got past the first interview (also if rejected later)."""
    effective_intent = func.coalesce(Email.manual_override, Email.intent)
    return select(Email.application_id).where(
        Email.application_id.is_not(None),
        effective_intent.in_(("next_round", "offer")),
    )


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

    reached_interview = session.execute(
        select(func.count(func.distinct(Application.id))).where(
            Application.id.in_(_interviewed_app_ids())
        )
    ).scalar_one()

    return StatsOut(
        total_applied=sum(by_status.values()),
        awaiting_response=total(_AWAITING),
        interviews=reached_interview,
        offers=by_status.get(Status.OFFER.value, 0),
        rejections=by_status.get(Status.REJECTION.value, 0),
        ghosted=by_status.get(Status.GHOSTED.value, 0),
    )


@router.get("", response_model=list[ApplicationOut])
def list_applications(
    status: str | None = Query(None, description="Filter by current status."),
    stage: str | None = Query(
        None,
        pattern="^(interview|awaiting|next_round)$",
        description="'interview': every application that had an interview, whatever "
        "happened afterwards (ongoing, rejected, offer). 'awaiting': still waiting for "
        "an answer (sent or acknowledged, not yet ghosted).",
    ),
    language: str | None = Query(None, description="Filter by application language (de/en)."),
    sort: str = Query("last_event_at", description="Sort field."),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    session: Session = Depends(get_session),
) -> list[Application]:
    # Emails are needed for `reached_interview`; load them in one query.
    stmt = select(Application).options(selectinload(Application.emails))
    if status:
        stmt = stmt.where(Application.current_status == status)
    if stage == "interview":
        stmt = stmt.where(Application.id.in_(_interviewed_app_ids()))
    elif stage == "next_round":
        stmt = stmt.where(Application.id.in_(_next_round_app_ids()))
    elif stage == "awaiting":
        stmt = stmt.where(Application.current_status.in_(_AWAITING))
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
