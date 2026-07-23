from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=3, max_length=20000)
    severity: str = Field("P3 - Moderate", max_length=20)
    service_name: str = Field(..., min_length=2, max_length=120)
    commander_name: str = Field("DevOps On-Call", max_length=120)
    impact_summary: str = Field("", max_length=2000)


class IncidentUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = Field(None, min_length=3, max_length=20000)
    severity: str | None = Field(None, max_length=20)
    status: str | None = Field(None, max_length=40)
    commander_name: str | None = Field(None, max_length=120)
    impact_summary: str | None = Field(None, max_length=2000)


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    incident_number: str
    organisation_id: UUID
    title: str
    description: str
    severity: str
    service_name: str
    status: str
    commander_name: str
    impact_summary: str
    created_at: datetime
    resolved_at: datetime | None = None
