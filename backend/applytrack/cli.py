"""`applytrack` command-line interface.

Commands:
    applytrack connect   — run the Gmail OAuth flow (with account verification)
    applytrack sync      — pull and classify new mail
    applytrack serve     — run the FastAPI server
    applytrack seed      — load the anonymized sample dataset (no Gmail needed)
"""

from __future__ import annotations

import logging
import sys

import typer
from rich.console import Console
from rich.table import Table

from .config import get_settings
from .db import init_db, session_scope
from .gmail.auth import GmailAuthError, connect_account, disconnect_account
from .gmail.sync import sync_mailbox

# Windows consoles default to a legacy code page that can't encode the glyphs
# Rich uses; force UTF-8 so output is identical across platforms and when piped.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass

app = typer.Typer(help="ApplyTrack — bilingual job-application email tracker.", no_args_is_help=True)
console = Console()

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


@app.command()
def connect(
    email: str = typer.Argument(
        None, help="The Gmail address to track. Defaults to the last connected account."
    ),
) -> None:
    """Authorize a Gmail account (read-only) and verify it matches EMAIL."""
    from .models import SyncState

    init_db()
    with session_scope() as session:
        state = session.get(SyncState, 1)
        email = email or (state.email_address if state else None)
        if not email:
            console.print("[bold red]✗[/] Please pass the Gmail address: applytrack connect you@gmail.com")
            raise typer.Exit(code=1)
        try:
            address = connect_account(email)
        except GmailAuthError as exc:  # includes AccountMismatchError
            console.print(f"[bold red]✗[/] {exc}")
            raise typer.Exit(code=1) from exc
        if state is None:
            state = SyncState(id=1)
            session.add(state)
        state.email_address = address
    console.print(f"[bold green]✓[/] Connected and verified [bold]{address}[/].")


@app.command()
def disconnect() -> None:
    """Delete the cached OAuth token."""
    removed = disconnect_account()
    console.print("[green]✓ Disconnected.[/]" if removed else "No account was connected.")


@app.command()
def sync(full: bool = typer.Option(False, "--full", help="Force a full re-sync.")) -> None:
    """Pull new mail, classify it, and recompute application statuses."""
    init_db()
    with session_scope() as session:
        result = sync_mailbox(session, full=full)
    console.print(f"[bold green]✓[/] {result.message}")


@app.command()
def reclassify() -> None:
    """Re-classify stored emails with the current logic (no Gmail sync)."""
    from .reclassify import reclassify_all

    init_db()
    with session_scope() as session:
        r = reclassify_all(session)
    console.print(
        f"[bold green]✓[/] Reclassified {r.total} email(s): "
        f"{r.changed} changed, {r.skipped_overrides} override(s) kept, "
        f"rebuilt into {r.applications} application(s)."
    )


@app.command()
def seed() -> None:
    """Load the anonymized DE/EN sample dataset so the UI runs without Gmail."""
    from .sample_data.loader import load_sample_data

    init_db()
    with session_scope() as session:
        count = load_sample_data(session)
    console.print(f"[bold green]✓[/] Loaded {count} sample email(s).")


@app.command()
def status() -> None:
    """Show a quick summary of tracked applications."""
    from sqlalchemy import select

    from .models import Application

    init_db()
    with session_scope() as session:
        apps = session.execute(select(Application).order_by(Application.last_event_at.desc())).scalars().all()
        table = Table(title="ApplyTrack")
        table.add_column("Company", style="bold")
        table.add_column("Role")
        table.add_column("Status")
        table.add_column("Lang")
        for a in apps:
            table.add_row(a.company, a.role or "—", a.current_status, a.language)
    console.print(table)


@app.command(name="app")
def desktop() -> None:
    """Open ApplyTrack as a native desktop window (requires a built frontend)."""
    init_db()
    from .desktop import run_desktop

    try:
        run_desktop()
    except RuntimeError as exc:
        console.print(f"[bold red]✗[/] {exc}")
        raise typer.Exit(code=1) from exc


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Bind host."),
    port: int = typer.Option(8000, help="Bind port."),
    reload: bool = typer.Option(False, "--reload", help="Auto-reload (dev)."),
) -> None:
    """Run the ApplyTrack API server."""
    import uvicorn

    get_settings()  # validate config early
    uvicorn.run("applytrack.api.app:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    app()
