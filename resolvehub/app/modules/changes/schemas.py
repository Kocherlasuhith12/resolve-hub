from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChangeCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field("", max_length=20000)
    change_type: str = Field("Normal", max_length=40)
    risk_level: str = Field("Medium", max_length=40)
    owner_name: str = Field("DevOps Team", max_length=120)
    maintenance_window: str = Field("Sat 02:00 - 04:00 UTC", max_length=120)


class ChangeUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = Field(None, max_length=20000)
    change_type: str | None = Field(None, max_length=40)
    risk_level: str | None = Field(None, max_length=40)
    status: str | None = Field(None, max_length=40)
    owner_name: str | None = Field(None, max_length=120)
    maintenance_window: str | None = Field(None, max_length=120)


class ChangeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    change_number: str
    organisation_id: UUID
    title: str
    description: str
    change_type: str
    risk_level: str
    status: str
    owner_name: str
    maintenance_window: str
    created_at: datetime
