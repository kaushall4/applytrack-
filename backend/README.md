# ApplyTrack — backend

FastAPI + SQLAlchemy backend for ApplyTrack. See the [root README](../README.md) for the
full project overview, screenshots, and setup.

## Install

```bash
python -m venv .venv
. .venv/Scripts/activate      # Windows  (use `source .venv/bin/activate` elsewhere)
pip install -e ".[dev]"
```

## CLI

```bash
applytrack connect you@gmail.com   # OAuth + account verification
applytrack sync [--full]           # pull & classify new mail
applytrack serve [--reload]        # run the API (http://localhost:8000)
applytrack seed                    # load the anonymized DE/EN sample dataset
applytrack status                  # quick table of tracked applications
```

## Layout

| Path                       | Responsibility                                        |
| -------------------------- | ----------------------------------------------------- |
| `applytrack/config.py`     | Settings from `.env` (DB URL, model, thresholds)      |
| `applytrack/db.py`         | Engine/session; SQLite now, Postgres-ready            |
| `applytrack/models.py`     | `applications`, `emails`, `sync_state` tables         |
| `applytrack/gmail/`        | Read-only OAuth (`auth.py`) and sync (`sync.py`)      |
| `applytrack/classify/`     | LLM + bilingual heuristic classifier + prompts        |
| `applytrack/grouping.py`   | Group emails into one application per company/role     |
| `applytrack/status.py`     | Status state machine + ghosting                        |
| `applytrack/api/`          | FastAPI app and routes                                 |
| `applytrack/sample_data/`  | Anonymized seed data + loader                          |

## Tests

```bash
ruff check .
pytest -q
```

`tests/fixtures/` holds German + English fixture emails covering every intent.
