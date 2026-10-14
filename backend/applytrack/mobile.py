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
    segno.make(data, error="m").save(buf, kind="svg", scale=6, border=3,
                                     dark="#111111", light="#ffffff", xmldecl=False)
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
