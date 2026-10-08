"""Pydantic schemas for the API surface (request/response models)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EmailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    gmail_id: str
    thread_id: str
    direction: str
    sender: str
    subject: str
    body_snippet: str
    received_at: datetime
    intent: str
    effective_intent: str
    confidence: float
    language: str
    classifier_source: str
    manual_override: str | None = None


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company: str
    role: str | None
    first_applied_at: datetime | None
    last_event_at: datetime | None
    current_status: str
    email_count: int
    language: str


class ApplicationDetailOut(ApplicationOut):
    emails: list[EmailOut] = Field(default_factory=list)


class StatsOut(BaseModel):
    total_applied: int
    awaiting_response: int
    interviews: int
    offers: int
    rejections: int
    ghosted: int


class OverrideIn(BaseModel):
    """Manual correction of an email's intent. ``null`` clears the override."""

    intent: str | None = None


class ConnectIn(BaseModel):
    email_address: str = Field(..., description="The Gmail address the user intends to track.")


class AccountStatusOut(BaseModel):
    connected: bool
    # True when an account was connected but Google no longer accepts its token;
    # the UI then offers a one-click reconnect for ``email_address``.
    session_expired: bool = False
    email_address: str | None = None
    last_synced_at: datetime | None = None


class SyncResultOut(BaseModel):
    new_emails: int
    classified: int
    applications: int
    message: str


class MessageOut(BaseModel):
    message: str
