from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    description: str | None = None
    logo_url: str | None = None
    address: str | None = None
    timezone: str = "UTC"
    language: str = "en"
    business_hours: str = "09:00 - 17:00"
    working_days: str = "Mon, Tue, Wed, Thu, Fri"
    region: str = "us-east-1"
    is_active: bool = True
    created_at: datetime


class WorkspaceSettingsUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    address: str | None = Field(default=None, max_length=300)
    timezone: str | None = Field(default=None, max_length=60)
    language: str | None = Field(default=None, max_length=10)
    business_hours: str | None = Field(default=None, max_length=50)
    working_days: str | None = Field(default=None, max_length=100)
    region: str | None = Field(default=None, max_length=50)


class WorkspaceStatsResponse(BaseModel):
    total_members: int
    open_tickets: int
    total_articles: int
    storage_used_mb: float
