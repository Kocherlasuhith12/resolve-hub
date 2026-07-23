from uuid import UUID

from fastapi import APIRouter, Response

from resolvehub.app.core.dependencies import CurrentPrincipal, DbSession
from resolvehub.app.modules.analytics.schemas import AnalyticsSummaryResponse
from resolvehub.app.modules.analytics.service import export_tickets_csv, get_analytics_summary

router = APIRouter(prefix="/organisations/{organisation_id}/analytics", tags=["Analytics"])


@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def analytics_summary_get(
    organisation_id: UUID, principal: CurrentPrincipal, session: DbSession
) -> AnalyticsSummaryResponse:
    return await get_analytics_summary(
        session, actor_id=principal.user.id, organisation_id=organisation_id
    )


@router.get("/exports/tickets")
async def analytics_tickets_csv_export(
    organisation_id: UUID, principal: CurrentPrincipal, session: DbSession
) -> Response:
    csv_data = await export_tickets_csv(
        session, actor_id=principal.user.id, organisation_id=organisation_id
    )
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="tickets-org-{organisation_id}.csv"'
        },
    )
