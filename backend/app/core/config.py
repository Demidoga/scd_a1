"""Application configuration, loaded from environment variables / `.env`.

Single source of truth for every setting name used across the backend —
see docs/Milestones/milestone-1.md §G1 for the configuration-ownership
contract this mirrors. Don't read `os.environ` directly anywhere else.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Triage provider selection
    triage_provider: Literal["llm", "rules", "simulated"] = "simulated"
    llm_api_key: str = ""
    llm_model: str = "llama-3.1-8b-instant"

    # Database
    database_url: str = "postgresql+psycopg://civicpulse:civicpulse@localhost:5432/civicpulse"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Backend runtime
    backend_port: int = 8000
    log_level: str = "INFO"

    # Rate limiter
    rate_limit_requests: int = 10
    rate_limit_window_seconds: int = 60

    # Cache TTLs
    stats_cache_ttl_seconds: int = 30
    triage_cache_ttl_seconds: int = 86400


@lru_cache
def get_settings() -> Settings:
    return Settings()
