from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from resolvehub.app.modules.tickets.enums import TicketPriority


class CategoryCreate(BaseModel):
    department_id: UUID
    parent_id: UUID | None = None
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    default_priority: TicketPriority = TicketPriority.MEDIUM


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organisation_id: UUID
    department_id: UUID
    parent_id: UUID | None
    name: str
    description: str | None
    default_priority: TicketPriority
    is_active: bool


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    default_priority: TicketPriority | None = None
    is_active: bool | None = None
