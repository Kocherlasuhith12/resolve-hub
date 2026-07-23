import { createContext, useContext } from 'react'

export type ThemeMode = 'light' | 'dark' | 'system'
export type LayoutDensity = 'compact' | 'comfortable' | 'spacious'
export type FontSize = 'small' | 'medium' | 'large'
export type SidebarMode = 'expanded' | 'collapsed'

export type AppearanceSettings = {
  theme: ThemeMode
  accentColor: string
  density: LayoutDensity
  fontSize: FontSize
  enableAnimations: boolean
  enableGlassmorphism: boolean
  sidebarMode: SidebarMode
}

export type ThemeContextType = {
  settings: AppearanceSettings
  savedSettings: AppearanceSettings
  resolvedTheme: 'light' | 'dark'
  hasUnsavedChanges: boolean
  isSaving: boolean
  setTheme: (theme: ThemeMode) => void
  setAccentColor: (color: string) => void
  setDensity: (density: LayoutDensity) => void
  setFontSize: (size: FontSize) => void
  setEnableAnimations: (enable: boolean) => void
  setEnableGlassmorphism: (enable: boolean) => void
  setSidebarMode: (mode: SidebarMode) => void
  saveSettings: () => Promise<void>
  resetSettings: () => Promise<void>
}

export const DEFAULT_APPEARANCE_SETTINGS: AppearanceSettings = {
  theme: 'light',
  accentColor: '#16A34A',
  density: 'comfortable',
  fontSize: 'medium',
  enableAnimations: true,
  enableGlassmorphism: true,
  sidebarMode: 'expanded',
}

export const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function useTheme(): ThemeContextType {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}
