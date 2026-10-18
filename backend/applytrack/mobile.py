"""Phone access: pair a phone with the ApplyTrack server running on your PC.

The phone opens ApplyTrack in its browser and installs it as an app (PWA).
Requests from other devices must carry the secret pairing key; the key reaches
the phone through a QR code shown in the desktop app. Nothing leaves your home
network and nothing costs money.
"""

from __future__ import annotations

import hmac
import ipaddress
import logging
import os
import re
import secrets
import socket
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from .config import get_settings

logger = logging.getLogger("applytrack.mobile")

KEY_HEADER = "X-ApplyTrack-Key"
_LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}


def is_local_client(host: str | None) -> bool:
    """True for requests coming from this PC itself."""
    if not host:
        return False
    if host in _LOOPBACK_HOSTS:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def get_or_create_key() -> str:
    """The secret pairing key (created once, stored next to token.json)."""
    path = Path(get_settings().mobile_key_file)
    if path.exists():
        key = path.read_text(encoding="utf-8").strip()
        if key:
            return key
    key = secrets.token_urlsafe(24)
    path.write_text(key, encoding="utf-8")
    logger.info("Created a new phone pairing key.")
    return key


def key_is_valid(candidate: str | None) -> bool:
    return bool(candidate) and hmac.compare_digest(candidate, get_or_create_key())


# --- Short pairing code -------------------------------------------------------
# An app added to the iPhone home screen gets its own storage, separate from
# Safari. If the key from the QR link doesn't make it across, the user types a
# short code shown on the PC instead. Codes live in memory only, expire after
# a few minutes and die after a handful of wrong guesses.
PAIR_CODE_TTL = 10 * 60
PAIR_CODE_MAX_FAILURES = 5


@dataclass
class _PairCode:
    code: str
    expires_at: float
    failures: int = 0


_pair_code: _PairCode | None = None
_pair_lock = threading.Lock()


def current_pair_code() -> tuple[str, int]:
    """The active code and its remaining seconds (a new one when expired/used)."""
    global _pair_code
    with _pair_lock:
        now = time.monotonic()
        if _pair_code is None or _pair_code.expires_at <= now:
            _pair_code = _PairCode(f"{secrets.randbelow(10**6):06d}", now + PAIR_CODE_TTL)
        return _pair_code.code, int(_pair_code.expires_at - now)


def redeem_pair_code(candidate: str) -> str | None:
    """Exchange a valid code for the pairing key; the code is single-use."""
    global _pair_code
    candidate = "".join(ch for ch in candidate if ch.isdigit())
    with _pair_lock:
        pc = _pair_code
        if pc is None or pc.expires_at <= time.monotonic():
            return None
        if not hmac.compare_digest(candidate, pc.code):
            pc.failures += 1
            if pc.failures >= PAIR_CODE_MAX_FAILURES:
                _pair_code = None
            return None
        _pair_code = None
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
