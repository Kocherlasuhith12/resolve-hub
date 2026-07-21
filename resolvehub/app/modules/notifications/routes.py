from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from resolvehub.app.core.dependencies import CurrentPrincipal, DbSession
from resolvehub.app.modules.notifications.schemas import (
    NotificationListResponse,
    NotificationResponse,
)
from resolvehub.app.modules.notifications.service import list_notifications, mark_notification_read

router = APIRouter(prefix="/organisations/{organisation_id}/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationListResponse)
async def notifications_list(
    organisation_id: UUID,
    principal: CurrentPrincipal,
    session: DbSession,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> NotificationListResponse:
    items, next_cursor = await list_notifications(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        cursor=cursor,
        limit=limit,
    )
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(item) for item in items],
        next_cursor=next_cursor,
    )


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def notifications_read(
    organisation_id: UUID,
    notification_id: UUID,
    principal: CurrentPrincipal,
    session: DbSession,
) -> NotificationResponse:
    item = await mark_notification_read(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        notification_id=notification_id,
    )
    return NotificationResponse.model_validate(item)
