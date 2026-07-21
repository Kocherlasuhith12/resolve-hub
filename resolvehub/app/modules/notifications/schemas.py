from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    kind: str
    title: str
    body: str
    resource_type: str
    resource_id: UUID
    read_at: datetime | None
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    next_cursor: str | None
