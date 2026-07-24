from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from resolvehub.app.core.dependencies import DbSession
from resolvehub.app.modules.assets.schemas import AssetCreate, AssetResponse, AssetUpdate
from resolvehub.app.modules.assets.service import AssetService

router = APIRouter(prefix="/organisations/{organisation_id}/assets", tags=["assets"])


@router.get("", response_model=list[AssetResponse])
async def list_assets(
    organisation_id: UUID,
    session: DbSession,
    category: str | None = None,
    search: str | None = None,
) -> list[AssetResponse]:
    return await AssetService.list_assets(session, organisation_id, category, search)  # type: ignore[return-value]


@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    organisation_id: UUID,
    payload: AssetCreate,
    session: DbSession,
) -> AssetResponse:
    return await AssetService.create_asset(session, organisation_id, payload)  # type: ignore[return-value]


@router.patch("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    organisation_id: UUID,
    asset_id: UUID,
    payload: AssetUpdate,
    session: DbSession,
) -> AssetResponse:
    updated = await AssetService.update_asset(session, organisation_id, asset_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Asset not found")
    return updated  # type: ignore[return-value]
