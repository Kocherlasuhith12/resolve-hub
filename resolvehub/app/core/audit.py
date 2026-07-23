from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog

from resolvehub.app.core.metrics import metrics_collector

logger = structlog.get_logger("resolvehub.audit")


def log_audit_event(
    action: str,
    actor_id: UUID | str | None,
    organisation_id: UUID | str | None,
    resource_type: str,
    resource_id: UUID | str | None,
    metadata: dict[str, Any] | None = None,
) -> None:
    event_data = {
        "timestamp": datetime.now(UTC).isoformat(),
        "action": action,
        "actor_id": str(actor_id) if actor_id else None,
        "organisation_id": str(organisation_id) if organisation_id else None,
        "resource_type": resource_type,
        "resource_id": str(resource_id) if resource_id else None,
        "metadata": metadata or {},
    }
    logger.info("security_audit_event", **event_data)
    metrics_collector.record_audit_event(action)
