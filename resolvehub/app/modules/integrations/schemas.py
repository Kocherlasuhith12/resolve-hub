from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class APIKeyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    scopes: str = Field(default="*", max_length=255)
    expires_days: int | None = Field(default=None, ge=1, le=365)


class APIKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    key_prefix: str
    scopes: str
    created_at: datetime
    expires_at: datetime | None
    revoked_at: datetime | None
    raw_key: str | None = None


class WebhookCreate(BaseModel):
    url: HttpUrl
    events: str = Field(default="*", max_length=255)


class WebhookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    url: str
    events: str
    is_active: bool
    created_at: datetime
    raw_secret: str | None = None


class WebhookDeliveryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    subscription_id: UUID
    event_type: str
    payload: dict[str, Any]
    status_code: int | None
    response_body: str | None
    attempt: int
    delivered_at: datetime | None
    created_at: datetime
