from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from resolvehub.app.modules.tickets.enums import MalwareScanStatus


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organisation_id: UUID
    ticket_id: UUID
    uploaded_by_id: UUID
    original_filename: str
    content_type: str
    size_bytes: int
    upload_completed: bool
    scan_status: MalwareScanStatus
    created_at: datetime
