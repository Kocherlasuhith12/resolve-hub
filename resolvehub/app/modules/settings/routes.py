from fastapi import APIRouter

from resolvehub.app.core.dependencies import CurrentPrincipal
from resolvehub.app.modules.settings.schemas import (
    AppearanceSettingsResponse,
    AppearanceSettingsUpdate,
)
from resolvehub.app.modules.settings.service import (
    get_user_appearance_settings,
    reset_user_appearance_settings,
    update_user_appearance_settings,
)

router = APIRouter(tags=["Settings"])


@router.get("/settings/appearance", response_model=AppearanceSettingsResponse)
async def appearance_settings_get(
    principal: CurrentPrincipal,
) -> AppearanceSettingsResponse:
    return get_user_appearance_settings(principal.user.id)


@router.put("/settings/appearance", response_model=AppearanceSettingsResponse)
async def appearance_settings_update(
    payload: AppearanceSettingsUpdate,
    principal: CurrentPrincipal,
) -> AppearanceSettingsResponse:
    return update_user_appearance_settings(principal.user.id, payload)


@router.post("/settings/appearance/reset", response_model=AppearanceSettingsResponse)
async def appearance_settings_reset(
    principal: CurrentPrincipal,
) -> AppearanceSettingsResponse:
    return reset_user_appearance_settings(principal.user.id)
