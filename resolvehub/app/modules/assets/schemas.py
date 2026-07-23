from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AssetCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    category: str = Field("Laptop", max_length=80)
    status: str = Field("In Use", max_length=40)
    assigned_to_name: str = Field("Unassigned", max_length=120)
    serial_number: str = Field("", max_length=120)
    location: str = Field("Primary HQ", max_length=120)


class AssetUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=200)
    category: str | None = Field(None, max_length=80)
    status: str | None = Field(None, max_length=40)
    assigned_to_name: str | None = Field(None, max_length=120)
    serial_number: str | None = Field(None, max_length=120)
    location: str | None = Field(None, max_length=120)


class AssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_tag: str
    organisation_id: UUID
    name: str
    category: str
    status: str
    assigned_to_name: str
    serial_number: str
    location: str
    created_at: datetime
