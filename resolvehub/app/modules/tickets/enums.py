from enum import StrEnum


class TicketPriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TicketSource(StrEnum):
    WEB = "WEB"
    MOBILE = "MOBILE"
    EMAIL = "EMAIL"
    API = "API"
    IMPORT = "IMPORT"
    VOICE = "VOICE"
    INTEGRATION = "INTEGRATION"


class TicketStatus(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    TRIAGED = "TRIAGED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_FOR_REQUESTER = "WAITING_FOR_REQUESTER"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    ESCALATED = "ESCALATED"
    REOPENED = "REOPENED"
    CANCELLED = "CANCELLED"


class SlaState(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    WARNING = "WARNING"
    BREACHED = "BREACHED"
    COMPLETED = "COMPLETED"


class ActorType(StrEnum):
    HUMAN = "HUMAN"
    SYSTEM = "SYSTEM"
    WORKFLOW = "WORKFLOW"
    INTEGRATION = "INTEGRATION"
    AI = "AI"


class CommentKind(StrEnum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"


class MalwareScanStatus(StrEnum):
    PENDING = "PENDING"
    CLEAN = "CLEAN"
    INFECTED = "INFECTED"
    FAILED = "FAILED"
