"""SQLAlchemy ORM models: applications and emails.

An *application* is one company/role. *Emails* belong to an application and
carry the classified intent. ``current_status`` on an application is recomputed
(via :mod:`applytrack.status`) whenever its emails change.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company: Mapped[str] = mapped_column(String(255), index=True)
    role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Stable grouping key (normalised company + role) used to merge threads.
    group_key: Mapped[str] = mapped_column(String(512), unique=True, index=True)

    first_applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_event_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_status: Mapped[str] = mapped_column(String(40), default="application_sent")
    email_count: Mapped[int] = mapped_column(Integer, default=0)
    language: Mapped[str] = mapped_column(String(8), default="en")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    emails: Mapped[list[Email]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="Email.received_at",
    )

    @property
    def reached_interview(self) -> bool:
        """True if an interview happened at any point — even if a rejection followed."""
        return any(e.effective_intent in INTERVIEW_STAGE_INTENTS for e in self.emails)

    @property
    def interview_rounds(self) -> int:
        """Interview rounds reached for this job (kept after a rejection)."""
        from .rounds import count_interview_rounds

        return count_interview_rounds(self.emails)


# Intents meaning "you got (at least) to an interview".
INTERVIEW_STAGE_INTENTS = frozenset({"interview_invite", "next_round", "offer"})


class Email(Base):
    __tablename__ = "emails"
    __table_args__ = (UniqueConstraint("gmail_id", name="uq_emails_gmail_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gmail_id: Mapped[str] = mapped_column(String(255), index=True)
    thread_id: Mapped[str] = mapped_column(String(255), index=True)

    application_id: Mapped[int | None] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=True, index=True
    )

    direction: Mapped[str] = mapped_column(String(10), default="received")  # sent|received
    sender: Mapped[str] = mapped_column(String(512), default="")
    recipient: Mapped[str] = mapped_column(String(512), default="")
    subject: Mapped[str] = mapped_column(String(998), default="")
    # Snippet only — full bodies are never persisted (privacy).
    body_snippet: Mapped[str] = mapped_column(Text, default="")
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    intent: Mapped[str] = mapped_column(String(40), default="not_application_related")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    language: Mapped[str] = mapped_column(String(8), default="en")
    classifier_source: Mapped[str] = mapped_column(String(20), default="heuristic")
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Manual override of the intent always wins over the model.
    manual_override: Mapped[str | None] = mapped_column(String(40), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    application: Mapped[Application | None] = relationship(back_populates="emails")

    @property
    def effective_intent(self) -> str:
        """Manual override if present, else the classified intent."""
        return self.manual_override or self.intent


class SyncState(Base):
    """Single-row table tracking the connected account and incremental sync cursor."""

    __tablename__ = "sync_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    email_address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    last_history_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AppSecret(Base):
    """Small key/value store for state shared by the PC and the cloud copy.

    Holds the Gmail OAuth token, the phone pairing key and the short pairing
    code, so a cloud deployment that shares the database needs no extra setup.
    Lives in the (git-ignored / private) database, never in the repository.
    """

    __tablename__ = "app_secrets"

    name: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )
