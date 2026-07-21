from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="RH_", extra="ignore")

    environment: Literal["local", "test", "staging", "production"] = "local"
    debug: bool = False
    service_name: str = "resolvehub-api"
    database_url: str = "postgresql+asyncpg://resolvehub:resolvehub-local@localhost/resolvehub"
    redis_url: str = "redis://localhost:6379/0"
    temporal_address: str = "localhost:7234"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "resolvehub-sla"
    outbox_batch_size: int = Field(default=50, ge=1, le=500)
    jwt_secret: SecretStr = SecretStr("local-only-change-this-secret-32-chars")
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_ttl_minutes: int = Field(default=15, ge=1, le=60)
    refresh_token_ttl_days: int = Field(default=30, ge=1, le=90)
    browser_cookie_secure: bool = False
    email_verification_ttl_hours: int = Field(default=24, ge=1, le=72)
    ai_enabled: bool = False
    ai_provider: Literal["fake"] = "fake"
    ai_confidence_threshold: float = Field(default=0.65, ge=0, le=1)
    cors_origins: list[str] = []

    @field_validator("jwt_secret")
    @classmethod
    def validate_secret(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 32:
            raise ValueError("RH_JWT_SECRET must contain at least 32 characters")
        return value

    @model_validator(mode="after")
    def validate_browser_cookie_security(self) -> "Settings":
        if self.environment in {"staging", "production"} and not self.browser_cookie_secure:
            raise ValueError(
                "RH_BROWSER_COOKIE_SECURE must be true outside local/test environments"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
