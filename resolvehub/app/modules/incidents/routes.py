from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from resolvehub.app.core.dependencies import DbSession
from resolvehub.app.modules.incidents.schemas import (
    IncidentCreate,
    IncidentResponse,
    IncidentUpdate,
)
from resolvehub.app.modules.incidents.service import IncidentService

router = APIRouter(prefix="/organisations/{organisation_id}/incidents", tags=["incidents"])


@router.get("", response_model=list[IncidentResponse])
async def list_incidents(
    organisation_id: UUID,
    session: DbSession,
    severity: str | None = None,
):
    return await IncidentService.list_incidents(session, organisation_id, severity)


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(
    organisation_id: UUID,
    payload: IncidentCreate,
    session: DbSession,
):
    return await IncidentService.create_incident(session, organisation_id, payload)


@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    organisation_id: UUID,
    incident_id: UUID,
    payload: IncidentUpdate,
    session: DbSession,
):
    updated = await IncidentService.update_incident(session, organisation_id, incident_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Incident not found")
    return updated
