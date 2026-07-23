from pydantic import BaseModel


class AnalyticsSummaryResponse(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    closed_tickets: int
    tickets_by_priority: dict[str, int]
    tickets_by_category: dict[str, int]
    sla_breached_count: int
    sla_compliance_percent: float
