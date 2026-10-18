# ── ApplyTrack cloud copy: one container serving API + built frontend ───────
# Used by render.yaml. Data lives in an external Postgres (DATABASE_URL);
# the Gmail token and pairing key are read from that database.

FROM node:20-alpine AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    CLOUD_MODE=true \
    APPLYTRACK_STATIC_DIR=/app/static \
    GOOGLE_TOKEN_FILE=/tmp/token.json
WORKDIR /app
COPY backend/pyproject.toml backend/README.md ./
COPY backend/applytrack ./applytrack
RUN pip install ".[postgres]"
COPY --from=web /web/dist ./static

# Render injects $PORT.
CMD ["sh", "-c", "uvicorn applytrack.api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
