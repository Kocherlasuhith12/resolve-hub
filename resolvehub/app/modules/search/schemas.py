from pydantic import BaseModel

from resolvehub.app.modules.tickets.schemas import TicketResponse


class TicketSearchResponse(BaseModel):
    items: list[TicketResponse]
    next_cursor: str | None
