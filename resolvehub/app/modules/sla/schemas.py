from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from resolvehub.app.modules.sla.calculator import validate_timezone, validate_weekly_hours
from resolvehub.app.modules.tickets.enums import SlaState, TicketPriority


class CalendarCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    timezone: str = Field(min_length=1, max_length=64)
    weekly_hours: dict[str, list[list[str]]]

    @field_validator("timezone")
    @classmethod
    def timezone_exists(cls, value: str) -> str:
        validate_timezone(value)
        return value

    @field_validator("weekly_hours")
    @classmethod
    def hours_are_valid(cls, value: dict[str, list[list[str]]]) -> dict[str, list[list[str]]]:
        validate_weekly_hours(value)
        return value


class CalendarResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    organisation_id: UUID
    name: str
    timezone: str
    weekly_hours: dict[str, list[list[str]]]
    is_active: bool


class HolidayCreate(BaseModel):
    holiday_date: date
    name: str = Field(min_length=2, max_length=120)


class PolicyCreate(BaseModel):
    category_id: UUID
    calendar_id: UUID
    priority: TicketPriority
    first_response_minutes: int = Field(ge=1, le=525_600)
    resolution_minutes: int = Field(ge=1, le=2_102_400)
    warning_percent: int = Field(default=80, ge=1, le=99)
    pause_on_waiting: bool = True


class PolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    organisation_id: UUID
    category_id: UUID
    calendar_id: UUID
    priority: TicketPriority
    first_response_minutes: int
    resolution_minutes: int
    warning_percent: int
    pause_on_waiting: bool
    is_active: bool


class TicketSlaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    ticket_id: UUID
    policy_id: UUID
    state: SlaState
    started_at: datetime
    first_response_deadline: datetime
    resolution_deadline: datetime
    paused_at: datetime | None
    accumulated_pause_seconds: int
