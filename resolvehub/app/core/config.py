from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
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
    ai_provider: Literal["fake", "gemini"] = "gemini"
    ai_confidence_threshold: float = Field(default=0.65, ge=0, le=1)
    cors_origins: list[str] = []

    storage_provider: Literal["local", "s3"] = "local"
    storage_local_dir: str = "storage_data"
    s3_endpoint_url: str | None = None
    s3_bucket: str = "resolvehub-attachments"
    s3_access_key: SecretStr = SecretStr("minioadmin")
    s3_secret_key: SecretStr = SecretStr("minioadmin")
    s3_region: str = "us-east-1"

    serve_frontend: bool = False
    prometheus_enabled: bool = True

    stripe_secret_key: SecretStr = Field(
        default=SecretStr(""),
        validation_alias=AliasChoices("RH_STRIPE_SECRET_KEY", "STRIPE_SECRET_KEY"),
    )
    stripe_publishable_key: str = Field(
        default="",
        validation_alias=AliasChoices("RH_STRIPE_PUBLISHABLE_KEY", "STRIPE_PUBLISHABLE_KEY"),
    )
    stripe_webhook_secret: SecretStr = Field(
        default=SecretStr(""),
        validation_alias=AliasChoices("RH_STRIPE_WEBHOOK_SECRET", "STRIPE_WEBHOOK_SECRET"),
    )
    stripe_price_id_starter: str = Field(
        default="price_starter_free",
        validation_alias=AliasChoices("RH_STRIPE_PRICE_ID_STARTER", "STRIPE_PRICE_ID_STARTER"),
    )
    stripe_price_id_pro: str = Field(
        default="price_pro_monthly_49",
        validation_alias=AliasChoices("RH_STRIPE_PRICE_ID_PRO", "STRIPE_PRICE_ID_PRO"),
    )
    stripe_price_id_enterprise: str = Field(
        default="price_enterprise_custom",
        validation_alias=AliasChoices(
            "RH_STRIPE_PRICE_ID_ENTERPRISE", "STRIPE_PRICE_ID_ENTERPRISE"
        ),
    )

    @field_validator("jwt_secret")
    @classmethod
    def validate_secret(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 32:
            raise ValueError("RH_JWT_SECRET must contain at least 32 characters")
        return value

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        if value.startswith("postgresql://") and not value.startswith("postgresql+"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
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
