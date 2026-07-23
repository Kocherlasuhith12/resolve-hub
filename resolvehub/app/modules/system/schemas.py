from datetime import datetime

from pydantic import BaseModel


class ServiceHealthItem(BaseModel):
    name: str
    status: str  # "healthy" | "degraded" | "down"
    latency_ms: float
    message: str | None = None


class SystemHealthResponse(BaseModel):
    overall_status: str
    timestamp: datetime
    services: list[ServiceHealthItem]
    metrics: dict[str, str | int | float]


class SystemSecuritySettings(BaseModel):
    min_password_length: int = 12
    require_mfa: bool = False
    session_timeout_minutes: int = 60
    allow_google_login: bool = True
    allow_github_login: bool = True
    allow_microsoft_login: bool = False
    max_attachment_size_mb: int = 25


class AuditLogEntry(BaseModel):
    id: str
    actor_name: str
    actor_email: str
    action: str
    resource_type: str
    resource_id: str
    details: str
    ip_address: str
    timestamp: datetime
