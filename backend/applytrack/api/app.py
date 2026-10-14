"""FastAPI application factory.

Wires CORS for the Vite dev server and installs error handlers that return
clean JSON — never a raw stack trace — so the frontend can render friendly
toasts.
"""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ..config import get_settings
from ..db import init_db
from ..gmail.auth import AccountMismatchError, GmailAuthError, SessionExpiredError
from ..mobile import KEY_HEADER, is_local_client, key_is_valid
from .routes import account, applications, emails, mobile, sync

logger = logging.getLogger("applytrack.api")

# Actions that only make sense on the PC (OAuth opens a browser there; pairing
# shows the secret key).
_PC_ONLY_PATHS = ("/api/account/connect", "/api/account/disconnect", "/api/mobile")


def _frontend_dist() -> Path | None:
    """Locate the built frontend (``frontend/dist``), if present.

    Honoured first: the ``APPLYTRACK_STATIC_DIR`` env var. Otherwise the repo's
    ``frontend/dist`` relative to this file. Returns None when no build exists
    (e.g. during dev, where Vite serves the frontend instead).
    """
    override = os.environ.get("APPLYTRACK_STATIC_DIR")
    if override:
        path = Path(override)
        return path if (path / "index.html").is_file() else None

    # backend/applytrack/api/app.py → repo root is parents[3]
    dist = Path(__file__).resolve().parents[3] / "frontend" / "dist"
    return dist if (dist / "index.html").is_file() else None


def _mount_frontend(app: FastAPI) -> None:
    """Serve the built SPA: hashed assets verbatim, everything else → index.html.

    Registered AFTER the API routers, so ``/api/*`` always wins. The catch-all
    returns index.html for client-side routes (e.g. /review) so deep links and
    reloads work in the packaged desktop app.
    """
    dist = _frontend_dist()
    if dist is None:
        return

    assets = dist / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    index = dist / "index.html"

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str) -> FileResponse:
        candidate = dist / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index)


@asynccontextmanager
async def _lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="ApplyTrack API",
        version="0.1.0",
        description="Bilingual job-application email tracker.",
        lifespan=_lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Phone access guard ---
    # Requests from this PC are trusted. Any other device (your phone in the
    # home Wi-Fi) must send the pairing key; account/pairing actions stay PC-only.
    @app.middleware("http")
    async def _phone_guard(request: Request, call_next):
        path = request.url.path
        if path.startswith("/api/") and path != "/api/health":
            client = request.client.host if request.client else None
            if not is_local_client(client):
                if path.startswith(_PC_ONLY_PATHS):
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "Only available on the PC running ApplyTrack.",
                                 "code": "pc_only"},
                    )
                if not key_is_valid(request.headers.get(KEY_HEADER)):
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "This device is not paired with ApplyTrack yet.",
                                 "code": "pairing_required"},
                    )
        return await call_next(request)

    # --- Error handlers: friendly JSON, no stack traces in responses ---
    @app.exception_handler(AccountMismatchError)
    async def _mismatch(_: Request, exc: AccountMismatchError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(SessionExpiredError)
    async def _session_expired(_: Request, exc: SessionExpiredError) -> JSONResponse:
        return JSONResponse(
            status_code=401, content={"detail": str(exc), "code": "session_expired"}
        )

    @app.exception_handler(GmailAuthError)
    async def _auth_error(_: Request, exc: GmailAuthError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error: %s", type(exc).__name__)
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred. Please try again."},
        )

    @app.get("/api/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(account.router)
    app.include_router(sync.router)
    app.include_router(applications.router)
    app.include_router(emails.router)
    app.include_router(mobile.router)

    # Serve the built SPA last so it never shadows the API routes above.
    _mount_frontend(app)

    return app


app = create_app()
