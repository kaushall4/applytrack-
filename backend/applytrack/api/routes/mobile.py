"""Phone pairing endpoints (PC-only — enforced by the guard in app.py)."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...config import get_settings
from ...mobile import current_pair_code, enable_in_env, pairing_url, qr_svg, redeem_pair_code

router = APIRouter(prefix="/api/mobile", tags=["mobile"])
# Reachable by an unpaired phone (exempt from the key guard in app.py).
pair_router = APIRouter(prefix="/api/pair", tags=["mobile"])


class MobileStatusOut(BaseModel):
    # The running server listens in the home network (phone can connect).
    enabled: bool
    # Phone access was switched on but ApplyTrack must be restarted first.
    restart_required: bool = False
    url: str | None = None
    qr_svg: str | None = None
    # Short code to type into the installed app if the QR key didn't carry over.
    pair_code: str | None = None
    pair_code_expires_in: int | None = None


@router.get("", response_model=MobileStatusOut)
def mobile_status() -> MobileStatusOut:
    if not get_settings().mobile_access:
        # Switched on during this run (written to .env) → waiting for a restart.
        pending = os.environ.get("MOBILE_ACCESS", "").lower() == "true"
        return MobileStatusOut(enabled=False, restart_required=pending)
    url = pairing_url()
    code, expires_in = current_pair_code()
    return MobileStatusOut(
        enabled=True,
        url=url,
        qr_svg=qr_svg(url) if url else None,
        pair_code=code,
        pair_code_expires_in=expires_in,
    )


@router.post("/enable", response_model=MobileStatusOut)
def enable_mobile() -> MobileStatusOut:
    """Switch phone access on (written to .env; active after a restart)."""
    if get_settings().mobile_access:
        return mobile_status()
    enable_in_env()
    return MobileStatusOut(enabled=False, restart_required=True)


class PairIn(BaseModel):
    code: str


class PairOut(BaseModel):
    key: str


@pair_router.post("", response_model=PairOut)
def pair(body: PairIn) -> PairOut:
    """Trade the short code shown on the PC for the pairing key."""
    if not get_settings().mobile_access:
        raise HTTPException(status_code=404, detail="Phone access is switched off.")
    key = redeem_pair_code(body.code)
    if key is None:
        raise HTTPException(status_code=400, detail="Code is wrong or expired.")
    return PairOut(key=key)
