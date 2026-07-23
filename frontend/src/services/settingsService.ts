import type { AppearanceSettings } from '../theme/ThemeContext'

const LOCAL_STORAGE_KEY = 'resolvehub_appearance_settings'

export const settingsService = {
  loadLocalSettings(): AppearanceSettings | null {
    try {
      const raw = localStorage.getItem(LOCAL_STORAGE_KEY)
      if (raw) {
        return JSON.parse(raw) as AppearanceSettings
      }
    } catch {
      // Ignore localStorage errors
    }
    return null
  },

  saveLocalSettings(settings: AppearanceSettings): void {
    try {
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(settings))
    } catch {
      // Ignore localStorage write errors
    }
  },

  clearLocalSettings(): void {
    try {
      localStorage.removeItem(LOCAL_STORAGE_KEY)
    } catch {
      // Ignore localStorage errors
    }
  },

  async fetchRemoteSettings(requestFn: <T>(path: string) => Promise<T>): Promise<AppearanceSettings | null> {
    try {
      const data = await requestFn<{
        theme: 'light' | 'dark' | 'system'
        accent_color: string
        layout_density: 'compact' | 'comfortable' | 'spacious'
        font_size: 'small' | 'medium' | 'large'
        enable_animations: boolean
        enable_glassmorphism: boolean
        sidebar_mode: 'expanded' | 'collapsed'
      }>('/settings/appearance')

      return {
        theme: data.theme,
        accentColor: data.accent_color,
        density: data.layout_density,
        fontSize: data.font_size,
        enableAnimations: data.enable_animations,
        enableGlassmorphism: data.enable_glassmorphism,
        sidebarMode: data.sidebar_mode,
      }
    } catch {
      return null
    }
  },

  async updateRemoteSettings(
    requestFn: <T>(path: string, options?: RequestInit) => Promise<T>,
    settings: AppearanceSettings
  ): Promise<boolean> {
    try {
      await requestFn('/settings/appearance', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          theme: settings.theme,
          accent_color: settings.accentColor,
          layout_density: settings.density,
          font_size: settings.fontSize,
          enable_animations: settings.enableAnimations,
          enable_glassmorphism: settings.enableGlassmorphism,
          sidebar_mode: settings.sidebarMode,
        }),
      })
      return true
    } catch {
      return false
    }
  },

  async resetRemoteSettings(
    requestFn: <T>(path: string, options?: RequestInit) => Promise<T>
  ): Promise<boolean> {
    try {
      await requestFn('/settings/appearance/reset', {
        method: 'POST',
      })
      return true
    } catch {
      return false
    }
  },
}
