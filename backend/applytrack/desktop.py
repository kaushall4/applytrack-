"""Native desktop window for ApplyTrack.

Runs the FastAPI app (which also serves the built frontend) on a private
localhost port in a background thread, then opens a native PyWebView window
pointing at it. No browser tab, and no Node runtime is required at run time —
the frontend is pre-built into ``frontend/dist``.

Launch with ``applytrack app`` or ``python -m applytrack.desktop``.
"""

from __future__ import annotations

import logging
import socket
import threading
import time
from urllib.request import urlopen

import uvicorn

from .api.app import _frontend_dist
from .api.app import app as fastapi_app

logger = logging.getLogger("applytrack.desktop")

WINDOW_TITLE = "ApplyTrack"


class _ThreadedServer(uvicorn.Server):
    """A uvicorn server that skips signal handlers (we're off the main thread)."""

    def install_signal_handlers(self) -> None:  # noqa: D401 - override
        pass


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_until_ready(url: str, timeout: float = 15.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=1) as resp:  # noqa: S310 - localhost only
                if resp.status == 200:
                    return True
        except Exception:  # noqa: BLE001 - server still starting
            time.sleep(0.2)
    return False


def run_desktop(*, width: int = 1280, height: int = 860) -> None:
    """Start the server thread and open the native window (blocks until closed)."""
    import webview  # imported lazily so the rest of the CLI works without a GUI

    if _frontend_dist() is None:
        raise RuntimeError(
            "Frontend build not found. Run `npm run build` in the frontend/ "
            "directory first (this produces frontend/dist)."
        )

    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"

    config = uvicorn.Config(fastapi_app, host="127.0.0.1", port=port, log_level="warning")
    server = _ThreadedServer(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    if not _wait_until_ready(f"{base_url}/api/health"):
        server.should_exit = True
        raise RuntimeError("Backend did not start in time.")

    logger.info("ApplyTrack desktop window opening at %s", base_url)
    webview.create_window(WINDOW_TITLE, base_url, width=width, height=height, min_size=(940, 640), x=100, y=50)
    webview.start()

    # Window closed → shut the server down cleanly.
    server.should_exit = True


if __name__ == "__main__":
    run_desktop()
