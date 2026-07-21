from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from resolvehub.app.modules.tickets.enums import (
    ActorType,
    CommentKind,
    MalwareScanStatus,
    SlaState,
    TicketPriority,
    TicketSource,
    TicketStatus,
)


class TicketCreate(BaseModel):
    category_id: UUID
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3, max_length=20_000)
    priority: TicketPriority | None = None
    source: TicketSource = TicketSource.WEB

    @field_validator("title", "description")
    @classmethod
    def reject_unsafe_control_characters(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("NUL characters are not allowed")
        return value.strip()


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticket_number: str
    organisation_id: UUID
    requester_id: UUID
    department_id: UUID
    category_id: UUID
    assigned_agent_id: UUID | None
    title: str
    description: str
    priority: TicketPriority
    status: TicketStatus
    source: TicketSource
    sla_state: SlaState
    first_response_deadline: datetime | None
    resolution_deadline: datetime | None
    resolved_at: datetime | None
    closed_at: datetime | None
    version: int
    created_at: datetime
    updated_at: datetime


class TicketListResponse(BaseModel):
    items: list[TicketResponse]
    next_cursor: str | None


class TicketAssignment(BaseModel):
    assigned_agent_id: UUID
    version: int = Field(ge=1)


class AssignmentCandidateResponse(BaseModel):
    user_id: UUID
    display_name: str


class TicketTransition(BaseModel):
    status: TicketStatus
    version: int = Field(ge=1)
    reason: str | None = Field(default=None, min_length=2, max_length=500)


class CommentCreate(BaseModel):
    kind: CommentKind = CommentKind.PUBLIC
    body: str = Field(min_length=1, max_length=10_000)

    @field_validator("body")
    @classmethod
    def reject_unsafe_control_characters(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("NUL characters are not allowed")
        return value.strip()


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticket_id: UUID
    author_id: UUID
    kind: CommentKind
    body: str
    created_at: datetime
    edited_at: datetime | None


class CommentListResponse(BaseModel):
    items: list[CommentResponse]
    next_cursor: str | None


class TicketEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticket_id: UUID
    actor_id: UUID | None
    actor_type: ActorType
    event_type: str
    previous_values: dict[str, object] | None
    new_values: dict[str, object] | None
    event_metadata: dict[str, object]
    correlation_id: UUID
    created_at: datetime


class TicketEventListResponse(BaseModel):
    items: list[TicketEventResponse]
    next_cursor: str | None


class AttachmentCreate(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=3, max_length=120)
    size_bytes: int = Field(gt=0, le=10 * 1024 * 1024)


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticket_id: UUID
    original_filename: str
    content_type: str
    size_bytes: int
    upload_completed: bool
    scan_status: MalwareScanStatus
    created_at: datetime
