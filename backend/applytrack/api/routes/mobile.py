"""Phone pairing endpoints (PC-only — enforced by the guard in app.py)."""

from __future__ import annotations

import os

from fastapi import APIRouter
from pydantic import BaseModel

from ...config import get_settings
from ...mobile import enable_in_env, pairing_url, qr_svg

router = APIRouter(prefix="/api/mobile", tags=["mobile"])


class MobileStatusOut(BaseModel):
    # The running server listens in the home network (phone can connect).
    enabled: bool
    # Phone access was switched on but ApplyTrack must be restarted first.
    restart_required: bool = False
    url: str | None = None
    qr_svg: str | None = None


@router.get("", response_model=MobileStatusOut)
def mobile_status() -> MobileStatusOut:
    if not get_settings().mobile_access:
        # Switched on during this run (written to .env) → waiting for a restart.
        pending = os.environ.get("MOBILE_ACCESS", "").lower() == "true"
        return MobileStatusOut(enabled=False, restart_required=pending)
    url = pairing_url()
    return MobileStatusOut(enabled=True, url=url, qr_svg=qr_svg(url) if url else None)


@router.post("/enable", response_model=MobileStatusOut)
def enable_mobile() -> MobileStatusOut:
    """Switch phone access on (written to .env; active after a restart)."""
    if get_settings().mobile_access:
        return mobile_status()
    enable_in_env()
    return MobileStatusOut(enabled=False, restart_required=True)
