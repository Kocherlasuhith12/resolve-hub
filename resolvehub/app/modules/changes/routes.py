from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from resolvehub.app.core.dependencies import DbSession
from resolvehub.app.modules.changes.schemas import ChangeCreate, ChangeResponse, ChangeUpdate
from resolvehub.app.modules.changes.service import ChangeService

router = APIRouter(prefix="/organisations/{organisation_id}/changes", tags=["changes"])


@router.get("", response_model=list[ChangeResponse])
async def list_changes(
    organisation_id: UUID,
    session: DbSession,
):
    return await ChangeService.list_changes(session, organisation_id)


@router.post("", response_model=ChangeResponse, status_code=status.HTTP_201_CREATED)
async def create_change(
    organisation_id: UUID,
    payload: ChangeCreate,
    session: DbSession,
):
    return await ChangeService.create_change(session, organisation_id, payload)


@router.patch("/{change_id}", response_model=ChangeResponse)
async def update_change(
    organisation_id: UUID,
    change_id: UUID,
    payload: ChangeUpdate,
    session: DbSession,
):
    updated = await ChangeService.update_change(session, organisation_id, change_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Change request not found")
    return updated
