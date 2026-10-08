"""Load the anonymized sample dataset into the database.

Reuses the real classifier and grouping/status logic so the seeded data looks
exactly like synced data — only the source (a JSON file) differs from Gmail.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..classify.base import EmailInput, get_classifier
from ..gmail.sync import _recompute_application, application_for_email
from ..grouping import (
    counterparty_address,
    extract_job_ref,
    extract_role,
    extract_role_from_body,
    resolve_company,
)
from ..models import Email

_SEED_FILE = Path(__file__).with_name("seed.json")
_SNIPPET_LEN = 500


def load_sample_data(session: Session) -> int:
    """Insert sample emails (idempotent on gmail_id). Returns count inserted."""
    records = json.loads(_SEED_FILE.read_text(encoding="utf-8"))
    classifier = get_classifier()
    touched: set[int] = set()
    inserted = 0

    for rec in records:
        if _exists(session, rec["gmail_id"]):
            continue

        classification = classifier.classify(
            EmailInput(
                sender=rec["sender"],
                subject=rec["subject"],
                body=rec["body"],
                direction=rec["direction"],
            )
        )
        language = rec.get("language") or classification.language

        email = Email(
            gmail_id=rec["gmail_id"],
            thread_id=rec["thread_id"],
            direction=rec["direction"],
            sender=rec["sender"],
            recipient=rec.get("recipient", ""),
            subject=rec["subject"],
            body_snippet=rec["body"][:_SNIPPET_LEN],
            received_at=datetime.fromisoformat(rec["received_at"]),
            intent=classification.intent.value,
            confidence=classification.confidence,
            language=language,
            classifier_source=classification.source,
            reasoning=classification.reasoning,
        )

        if classification.intent.value != "not_application_related":
            company_address = counterparty_address(
                rec["direction"], rec["sender"], rec.get("recipient", "")
            )
            company = resolve_company(classification, company_address, rec["subject"])
            role = (
                classification.role
                or extract_role(rec["subject"], company)
                or extract_role_from_body(rec["body"], company)
            )
            ref = extract_job_ref(rec["subject"]) or extract_job_ref(rec["body"])
            email.application = application_for_email(
                session, rec["thread_id"], company, role, ref, language
            )

        session.add(email)
        session.flush()
        if email.application_id is not None:
            touched.add(email.application_id)
        inserted += 1

    for app_id in touched:
        _recompute_application(session, app_id)

    return inserted


def _exists(session: Session, gmail_id: str) -> bool:
    return session.execute(select(Email.id).where(Email.gmail_id == gmail_id)).first() is not None
