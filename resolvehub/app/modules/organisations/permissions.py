ORGANISATION_READ = "organisation:read"
ORGANISATION_UPDATE = "organisation:update"
MEMBER_INVITE = "member:invite"
MEMBER_READ = "member:read"
DEPARTMENT_CREATE = "department:create"
DEPARTMENT_UPDATE = "department:update"
CATEGORY_CREATE = "category:create"
CATEGORY_UPDATE = "category:update"
TICKET_CREATE = "ticket:create"
TICKET_READ = "ticket:read"
TICKET_READ_ALL = "ticket:read_all"
TICKET_UPDATE = "ticket:update"
TICKET_ASSIGN = "ticket:assign"
TICKET_TRANSITION = "ticket:transition"
TICKET_RESOLVE = "ticket:resolve"
TICKET_REOPEN = "ticket:reopen"
TICKET_ESCALATE = "ticket:escalate"
COMMENT_CREATE = "comment:create"
INTERNAL_NOTE_CREATE = "internal_note:create"
INTERNAL_NOTE_READ = "internal_note:read"
ATTACHMENT_CREATE = "attachment:create"
AUDIT_VIEW = "audit:view"
SLA_MANAGE = "sla:manage"
NOTIFICATION_READ = "notification:read"
AI_SUGGEST = "ai:suggest"
AI_REVIEW = "ai:review"
MEMBER_UPDATE = "member:update"
ANALYTICS_READ = "analytics:read"
APIKEY_MANAGE = "apikey:manage"
WEBHOOK_MANAGE = "webhook:manage"

ADMIN_PERMISSIONS = frozenset(
    {
        ORGANISATION_READ,
        ORGANISATION_UPDATE,
        MEMBER_INVITE,
        MEMBER_READ,
        MEMBER_UPDATE,
        DEPARTMENT_CREATE,
        DEPARTMENT_UPDATE,
        CATEGORY_CREATE,
        CATEGORY_UPDATE,
        TICKET_CREATE,
        TICKET_READ,
        TICKET_READ_ALL,
        TICKET_UPDATE,
        TICKET_ASSIGN,
        TICKET_TRANSITION,
        TICKET_RESOLVE,
        TICKET_REOPEN,
        TICKET_ESCALATE,
        COMMENT_CREATE,
        INTERNAL_NOTE_CREATE,
        INTERNAL_NOTE_READ,
        ATTACHMENT_CREATE,
        AUDIT_VIEW,
        SLA_MANAGE,
        NOTIFICATION_READ,
        AI_SUGGEST,
        AI_REVIEW,
        ANALYTICS_READ,
        APIKEY_MANAGE,
        WEBHOOK_MANAGE,
    }
)

AGENT_PERMISSIONS = frozenset(
    {
        ORGANISATION_READ,
        TICKET_CREATE,
        TICKET_READ,
        TICKET_READ_ALL,
        TICKET_UPDATE,
        TICKET_ASSIGN,
        TICKET_TRANSITION,
        TICKET_RESOLVE,
        TICKET_REOPEN,
        TICKET_ESCALATE,
        COMMENT_CREATE,
        INTERNAL_NOTE_CREATE,
        INTERNAL_NOTE_READ,
        ATTACHMENT_CREATE,
        NOTIFICATION_READ,
        AI_SUGGEST,
        AI_REVIEW,
    }
)

REQUESTER_PERMISSIONS = frozenset(
    {
        ORGANISATION_READ,
        TICKET_CREATE,
        TICKET_READ,
        COMMENT_CREATE,
        ATTACHMENT_CREATE,
        NOTIFICATION_READ,
    }
)

AUDITOR_PERMISSIONS = frozenset(
    {
        ORGANISATION_READ,
        TICKET_READ,
        TICKET_READ_ALL,
        INTERNAL_NOTE_READ,
        AUDIT_VIEW,
        NOTIFICATION_READ,
    }
)
