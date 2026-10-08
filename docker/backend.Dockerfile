# ── ApplyTrack backend ──────────────────────────────────────────────────────
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first for better layer caching.
COPY backend/pyproject.toml ./
COPY backend/applytrack ./applytrack
RUN pip install --upgrade pip && pip install .

# Default DB lives on a mounted volume so data survives container restarts.
ENV DATABASE_URL=sqlite:////data/applytrack.db
VOLUME ["/data"]

EXPOSE 8000

# 0.0.0.0 so the port is reachable from outside the container.
CMD ["uvicorn", "applytrack.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
