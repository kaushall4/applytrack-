"""Phone access: pair a phone with the ApplyTrack server running on your PC.

The phone opens ApplyTrack in its browser and installs it as an app (PWA).
Requests from other devices must carry the secret pairing key; the key reaches
the phone through a QR code shown in the desktop app. Nothing leaves your home
network and nothing costs money.
"""

from __future__ import annotations

import hmac
import ipaddress
import json
import logging
import os
import re
import secrets
import socket
import threading
import time
from pathlib import Path

from .config import get_settings
from .secret_store import MOBILE_KEY, PAIR_CODE, delete_secret, get_secret, set_secret

logger = logging.getLogger("applytrack.mobile")

KEY_HEADER = "X-ApplyTrack-Key"
_LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}


def is_local_client(host: str | None) -> bool:
    """True for requests coming from this PC itself (never in the cloud copy)."""
    if not host or get_settings().cloud_mode:
        return False
    if host in _LOOPBACK_HOSTS:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


_key_cache: str | None = None


def get_or_create_key() -> str:
    """The secret pairing key, shared by the PC and the cloud copy.

    Order: ``MOBILE_KEY`` setting → database → legacy ``mobile_access.key`` file
    (moved into the database) → newly generated.
    """
    global _key_cache
    configured = get_settings().mobile_key
    if configured:
        return configured
    if _key_cache:
        return _key_cache
    key = get_secret(MOBILE_KEY)
    if not key:
        path = Path(get_settings().mobile_key_file)
        legacy = path.read_text(encoding="utf-8").strip() if path.exists() else ""
        key = legacy or secrets.token_urlsafe(24)
        set_secret(MOBILE_KEY, key)
        logger.info("Phone pairing key %s.", "moved to the database" if legacy else "created")
    _key_cache = key
    return key


def key_is_valid(candidate: str | None) -> bool:
    return bool(candidate) and hmac.compare_digest(candidate, get_or_create_key())


# --- Short pairing code -------------------------------------------------------
# An app added to the iPhone home screen gets its own storage, separate from
# Safari. If the key from the QR link doesn't make it across, the user types a
# short code shown on the PC instead. Codes live in memory only, expire after
# a few minutes and die after a handful of wrong guesses.
# Kept in the database so a code shown on the PC also works against the cloud copy.
PAIR_CODE_TTL = 10 * 60
PAIR_CODE_MAX_FAILURES = 5

_pair_lock = threading.Lock()


def _load_pair_code() -> dict | None:
    raw = get_secret(PAIR_CODE)
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except ValueError:
        return None
    return data if data.get("expires_at", 0) > time.time() else None


def current_pair_code() -> tuple[str, int]:
    """The active code and its remaining seconds (a new one when expired/used)."""
    with _pair_lock:
        data = _load_pair_code()
        if data is None:
            data = {
                "code": f"{secrets.randbelow(10**6):06d}",
                "expires_at": time.time() + PAIR_CODE_TTL,
                "failures": 0,
            }
            set_secret(PAIR_CODE, json.dumps(data))
        return data["code"], int(data["expires_at"] - time.time())


def redeem_pair_code(candidate: str) -> str | None:
    """Exchange a valid code for the pairing key; the code is single-use."""
    candidate = "".join(ch for ch in candidate if ch.isdigit())
    with _pair_lock:
        data = _load_pair_code()
        if data is None:
            return None
        if not hmac.compare_digest(candidate, data["code"]):
            data["failures"] = data.get("failures", 0) + 1
            if data["failures"] >= PAIR_CODE_MAX_FAILURES:
                delete_secret(PAIR_CODE)
            else:
                set_secret(PAIR_CODE, json.dumps(data))
            return None
        delete_secret(PAIR_CODE)
    return get_or_create_key()


def lan_ip() -> str | None:
    """This PC's address in the local network (no traffic is actually sent)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("192.168.0.1", 9))
            ip = s.getsockname()[0]
    except OSError:
        return None
    return None if ip.startswith("127.") else ip


def pairing_url() -> str | None:
    cloud = get_settings().cloud_url
    if cloud:
        return f"{cloud.rstrip('/')}/?key={get_or_create_key()}"
    ip = lan_ip()
    if not ip:
        return None
    return f"http://{ip}:{get_settings().mobile_port}/?key={get_or_create_key()}"


def qr_svg(data: str) -> str:
    """QR code as an inline SVG (dark modules on a white quiet zone)."""
    import io

    import segno

    buf = io.BytesIO()
    # omitsize → viewBox only, so the code scales to its box instead of being
    # cropped (a cut-off finder pattern makes it unreadable). Border 4 = spec.
    segno.make(data, error="m").save(buf, kind="svg", border=4, omitsize=True,
                                     dark="#000000", light="#ffffff", xmldecl=False)
    return buf.getvalue().decode("utf-8")


def enable_in_env(env_path: str = ".env") -> None:
    """Persist ``MOBILE_ACCESS=true`` in .env (takes effect after a restart)."""
    path = Path(env_path)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    line = "MOBILE_ACCESS=true"
    if re.search(r"^MOBILE_ACCESS=.*$", text, flags=re.MULTILINE):
        text = re.sub(r"^MOBILE_ACCESS=.*$", line, text, flags=re.MULTILINE)
    else:
        text = (text.rstrip("\n") + "\n\n" if text else "") + (
            "# Phone app in the home Wi-Fi (pairing key required)\n" + line + "\n"
        )
    path.write_text(text, encoding="utf-8")
    os.environ["MOBILE_ACCESS"] = "true"
