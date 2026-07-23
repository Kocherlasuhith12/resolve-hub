from uuid import uuid4

from resolvehub.app.modules.settings.schemas import AppearanceSettingsUpdate
from resolvehub.app.modules.settings.service import (
    get_user_appearance_settings,
    reset_user_appearance_settings,
    update_user_appearance_settings,
)


def test_appearance_settings_default():
    user_id = uuid4()
    settings = get_user_appearance_settings(user_id)
    assert settings.theme == "light"
    assert settings.accent_color == "#16A34A"
    assert settings.layout_density == "comfortable"
    assert settings.font_size == "medium"
    assert settings.enable_animations is True
    assert settings.enable_glassmorphism is True


def test_appearance_settings_update():
    user_id = uuid4()
    update_user_appearance_settings(
        user_id,
        AppearanceSettingsUpdate(
            theme="dark",
            accent_color="#2563EB",
            layout_density="compact",
            font_size="large",
            enable_animations=False,
        ),
    )

    settings = get_user_appearance_settings(user_id)
    assert settings.theme == "dark"
    assert settings.accent_color == "#2563EB"
    assert settings.layout_density == "compact"
    assert settings.font_size == "large"
    assert settings.enable_animations is False


def test_appearance_settings_reset():
    user_id = uuid4()
    update_user_appearance_settings(
        user_id,
        AppearanceSettingsUpdate(theme="dark", accent_color="#DC2626"),
    )
    res = reset_user_appearance_settings(user_id)
    assert res.theme == "light"
    assert res.accent_color == "#16A34A"
