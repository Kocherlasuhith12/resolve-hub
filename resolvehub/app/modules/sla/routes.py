from uuid import UUID

from fastapi import APIRouter, status

from resolvehub.app.core.dependencies import CurrentPrincipal, DbSession
from resolvehub.app.modules.sla.schemas import (
    CalendarCreate,
    CalendarResponse,
    HolidayCreate,
    PolicyCreate,
    PolicyResponse,
)
from resolvehub.app.modules.sla.service import (
    add_holiday,
    create_calendar,
    create_policy,
    list_calendars,
    list_policies,
)

router = APIRouter(prefix="/organisations/{organisation_id}/sla", tags=["SLA"])


@router.post("/calendars", response_model=CalendarResponse, status_code=status.HTTP_201_CREATED)
async def calendars_create(
    organisation_id: UUID,
    payload: CalendarCreate,
    principal: CurrentPrincipal,
    session: DbSession,
) -> CalendarResponse:
    item = await create_calendar(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        **payload.model_dump(),
    )
    return CalendarResponse.model_validate(item)


@router.get("/calendars", response_model=list[CalendarResponse])
async def calendars_list(
    organisation_id: UUID, principal: CurrentPrincipal, session: DbSession
) -> list[CalendarResponse]:
    items = await list_calendars(
        session, actor_id=principal.user.id, organisation_id=organisation_id
    )
    return [CalendarResponse.model_validate(item) for item in items]


@router.post("/calendars/{calendar_id}/holidays", status_code=status.HTTP_204_NO_CONTENT)
async def holidays_create(
    organisation_id: UUID,
    calendar_id: UUID,
    payload: HolidayCreate,
    principal: CurrentPrincipal,
    session: DbSession,
) -> None:
    await add_holiday(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        calendar_id=calendar_id,
        holiday_date=payload.holiday_date,
        name=payload.name,
    )


@router.post("/policies", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def policies_create(
    organisation_id: UUID,
    payload: PolicyCreate,
    principal: CurrentPrincipal,
    session: DbSession,
) -> PolicyResponse:
    item = await create_policy(
        session,
        actor_id=principal.user.id,
        organisation_id=organisation_id,
        **payload.model_dump(),
    )
    return PolicyResponse.model_validate(item)


@router.get("/policies", response_model=list[PolicyResponse])
async def policies_list(
    organisation_id: UUID, principal: CurrentPrincipal, session: DbSession
) -> list[PolicyResponse]:
    items = await list_policies(
        session, actor_id=principal.user.id, organisation_id=organisation_id
    )
    return [PolicyResponse.model_validate(item) for item in items]
