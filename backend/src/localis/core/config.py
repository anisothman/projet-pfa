"""Application settings loaded from environment / .env.

check_keys() is called at startup in localis.main so failures surface early instead of on first request.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API keys
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    serp_api_key: str | None = None

    # LLM routing
    llm_primary: Literal["openai", "gemini"] = "openai"
    openai_model: str = "gpt-4o-mini"
    gemini_model: str = "gemini-2.0-flash"

    # Storage
    reports_dir: Path = Field(default=Path("./reports"))

    # Observability
    log_level: str = "INFO"
    log_json: bool = False

    # HTTP
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def check_keys(self) -> None:
        """Fail-fast if required keys are missing. Called at app startup."""
        missing: list[str] = []
        if not self.serp_api_key:
            missing.append("SERP_API_KEY")
        # Need at least one LLM key — router picks the other as fallback if present.
        if not self.openai_api_key and not self.gemini_api_key:
            missing.append("OPENAI_API_KEY or GEMINI_API_KEY")
        if missing:
            raise RuntimeError("Missing required environment variables: " + ", ".join(missing))


@lru_cache
def get_settings() -> Settings:
    return Settings()
