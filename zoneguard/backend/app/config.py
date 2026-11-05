from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ZG_", env_file=".env", extra="ignore")

    environment: str = "development"  # development | test | production
    database_url: str = "postgresql+psycopg://zoneguard@localhost:5432/zoneguard"  # set ZG_DATABASE_URL
    # Comma-separated Fernet keys. First key encrypts; all keys decrypt (supports rotation).
    encryption_keys: str = Field(default="", repr=False)
    public_base_url: str = "http://localhost:3000"
    cookie_secure: bool = False
    session_ttl_hours: int = 12
    session_idle_minutes: int = 120

    storage_dir: Path = Path("./data/uploads")
    model_dir: Path = Path("../models")
    default_person_model: str = "yolox_tiny"
    max_upload_mb: int = 500
    max_video_duration_s: int = 1800
    analysis_sample_fps: float = 5.0
    analysis_workers: int = 1

    # Email (SMTP). backend: smtp | console | memory
    email_backend: str = "console"
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_username: str = ""
    smtp_password: str = Field(default="", repr=False)
    smtp_starttls: bool = False
    smtp_use_ssl: bool = False
    email_from: str = "ZoneGuard AI <alerts@zoneguard.local>"

    rate_limit_login_per_minute: int = 10
    rate_limit_register_per_hour: int = 5
    rate_limit_default_per_minute: int = 600
    retention_sweep_interval_s: int = 3600
    run_background_tasks: bool = True
    trusted_proxy_count: int = 0

    @field_validator("environment")
    @classmethod
    def _env(cls, v: str) -> str:
        if v not in {"development", "test", "production"}:
            raise ValueError("environment must be development, test or production")
        return v

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    def validate_for_runtime(self) -> None:
        if not self.encryption_keys:
            raise RuntimeError(
                "ZG_ENCRYPTION_KEYS is not set. Generate one with: "
                "python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )
        if self.is_production and not self.cookie_secure:
            raise RuntimeError("ZG_COOKIE_SECURE must be true in production (HTTPS only)")
        if self.is_production and self.email_backend in {"console", "memory"}:
            raise RuntimeError("Configure a real ZG_EMAIL_BACKEND=smtp in production")


@lru_cache
def get_settings() -> Settings:
    return Settings()
