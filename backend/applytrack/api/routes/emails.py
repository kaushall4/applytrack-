"""Email endpoints: needs-review queue, noise list, and manual overrides."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...classify.base import Intent
from ...config import get_settings
from ...db import get_session
from ...gmail.sync import _recompute_application
from ...models import Email
from ...schemas import EmailOut, OverrideIn

router = APIRouter(prefix="/api/emails", tags=["emails"])


@router.get("/needs-review", response_model=list[EmailOut])
def needs_review(session: Session = Depends(get_session)) -> list[Email]:
    """Low-confidence, application-related classifications awaiting correction."""
    threshold = get_settings().review_confidence_threshold
    stmt = (
        select(Email)
        .where(Email.confidence < threshold)
        .where(Email.manual_override.is_(None))
        .where(Email.intent != Intent.NOT_APPLICATION_RELATED.value)
        .order_by(Email.confidence.asc())
    )
    return list(session.execute(stmt).scalars().all())


@router.get("/noise", response_model=list[EmailOut])
def noise(session: Session = Depends(get_session)) -> list[Email]:
    """Mail filtered out as not-application-related (kept, never silently dropped)."""
    stmt = (
        select(Email)
        .where(Email.intent == Intent.NOT_APPLICATION_RELATED.value)
        .order_by(Email.received_at.desc())
    )
    return list(session.execute(stmt).scalars().all())


@router.patch("/{email_id}/override", response_model=EmailOut)
def set_override(
    email_id: int,
    payload: OverrideIn,
    session: Session = Depends(get_session),
) -> Email:
    """Manually set or clear an email's intent. Overrides always win over the model."""
    email = session.get(Email, email_id)
    if email is None:
        raise HTTPException(status_code=404, detail="Email not found.")

    if payload.intent is None:
        email.manual_override = None
    else:
        # Validate against the taxonomy.
        try:
            email.manual_override = Intent(payload.intent).value
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Unknown intent.") from exc

    session.add(email)
    session.flush()

    if email.application_id is not None:
        _recompute_application(session, email.application_id)
    session.commit()
    session.refresh(email)
    return email
