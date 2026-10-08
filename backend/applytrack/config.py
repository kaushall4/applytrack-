"""Application configuration, loaded from environment / `.env`.

All tunables live here so the rest of the codebase never reads `os.environ`
directly. Swapping SQLite for Postgres is purely a `DATABASE_URL` change.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Anthropic ---
    anthropic_api_key: str | None = None
    applytrack_model: str = "claude-haiku-4-5"

    # --- Database ---
    database_url: str = "sqlite:///./applytrack.db"

    # --- Gmail OAuth ---
    google_credentials_file: str = "credentials.json"
    google_token_file: str = "token.json"

    # --- Behaviour ---
    ghost_threshold_days: int = 21
    review_confidence_threshold: float = 0.6
    frontend_origin: str = "http://localhost:5173"

    # Comma-separated sender/recipient substrings (domains or addresses) to treat
    # as not-application-related, e.g. recruiting agencies: "agency.example,acme-hr.example".
    ignored_senders: str = ""

    @property
    def llm_enabled(self) -> bool:
        """LLM classification is available only when an API key is configured."""
        return bool(self.anthropic_api_key)

    @property
    def ignored_list(self) -> list[str]:
        """Parsed, lowercased ignore patterns."""
        return [p.strip().lower() for p in self.ignored_senders.split(",") if p.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
