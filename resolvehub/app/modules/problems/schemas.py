from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProblemCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    category: str = Field("Infrastructure", max_length=80)
    root_cause: str = Field("", max_length=5000)
    workaround: str = Field("", max_length=5000)
    impacted_incidents_count: int = Field(1, ge=0)


class ProblemUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=200)
    category: str | None = Field(None, max_length=80)
    status: str | None = Field(None, max_length=40)
    root_cause: str | None = Field(None, max_length=5000)
    workaround: str | None = Field(None, max_length=5000)
    impacted_incidents_count: int | None = Field(None, ge=0)


class ProblemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    problem_number: str
    organisation_id: UUID
    title: str
    category: str
    status: str
    root_cause: str
    workaround: str
    impacted_incidents_count: int
    created_at: datetime
