from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ThemeMode = Literal["light", "dark", "system"]
AccentColor = Literal["emerald", "blue", "purple", "orange", "red"]
LayoutDensity = Literal["compact", "comfortable", "spacious"]
FontSize = Literal["small", "medium", "large"]
SidebarMode = Literal["expanded", "collapsed"]


class AppearanceSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    theme: ThemeMode = "light"
    accent_color: str = "#16A34A"
    layout_density: LayoutDensity = "comfortable"
    font_size: FontSize = "medium"
    enable_animations: bool = True
    enable_glassmorphism: bool = True
    sidebar_mode: SidebarMode = "expanded"


class AppearanceSettingsUpdate(BaseModel):
    theme: ThemeMode | None = None
    accent_color: str | None = Field(default=None, max_length=30)
    layout_density: LayoutDensity | None = None
    font_size: FontSize | None = None
    enable_animations: bool | None = None
    enable_glassmorphism: bool | None = None
    sidebar_mode: SidebarMode | None = None
