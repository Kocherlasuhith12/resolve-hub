from typing import Any
from uuid import UUID

from resolvehub.app.modules.settings.schemas import (
    AppearanceSettingsResponse,
    AppearanceSettingsUpdate,
)

# In-memory thread-safe user appearance settings registry
_USER_SETTINGS_STORE: dict[UUID, dict[str, Any]] = {}

DEFAULT_APPEARANCE_SETTINGS = {
    "theme": "light",
    "accent_color": "#16A34A",
    "layout_density": "comfortable",
    "font_size": "medium",
    "enable_animations": True,
    "enable_glassmorphism": True,
    "sidebar_mode": "expanded",
}


def get_user_appearance_settings(user_id: UUID) -> AppearanceSettingsResponse:
    stored = _USER_SETTINGS_STORE.get(user_id)
    if not stored:
        return AppearanceSettingsResponse(**DEFAULT_APPEARANCE_SETTINGS)
    return AppearanceSettingsResponse(**stored)


def update_user_appearance_settings(
    user_id: UUID, payload: AppearanceSettingsUpdate
) -> AppearanceSettingsResponse:
    current = _USER_SETTINGS_STORE.get(user_id, DEFAULT_APPEARANCE_SETTINGS.copy()).copy()

    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        if v is not None:
            current[k] = v

    _USER_SETTINGS_STORE[user_id] = current
    return AppearanceSettingsResponse(**current)


def reset_user_appearance_settings(user_id: UUID) -> AppearanceSettingsResponse:
    _USER_SETTINGS_STORE[user_id] = DEFAULT_APPEARANCE_SETTINGS.copy()
    return AppearanceSettingsResponse(**DEFAULT_APPEARANCE_SETTINGS)
