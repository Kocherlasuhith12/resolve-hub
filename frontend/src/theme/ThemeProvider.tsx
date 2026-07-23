import { useState, useEffect, useCallback, type ReactNode } from 'react'
import {
  ThemeContext,
  DEFAULT_APPEARANCE_SETTINGS,
  type AppearanceSettings,
  type ThemeMode,
  type LayoutDensity,
  type FontSize,
  type SidebarMode,
} from './ThemeContext'
import { settingsService } from '../services/settingsService'
import { useAuth } from '../auth/useAuth'

export function ThemeProvider({ children }: { children: ReactNode }) {
  const { status, request } = useAuth()

  const [settings, setSettings] = useState<AppearanceSettings>(() => {
    return settingsService.loadLocalSettings() || DEFAULT_APPEARANCE_SETTINGS
  })

  const [savedSettings, setSavedSettings] = useState<AppearanceSettings>(settings)
  const [systemDark, setSystemDark] = useState<boolean>(() => {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
  })
  const [isSaving, setIsSaving] = useState(false)

  // Listen for OS color scheme changes
  useEffect(() => {
    if (!window.matchMedia) return
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = (e: MediaQueryListEvent) => setSystemDark(e.matches)
    mediaQuery.addEventListener('change', handler)
    return () => mediaQuery.removeEventListener('change', handler)
  }, [])

  // Sync with backend when authenticated
  useEffect(() => {
    if (status === 'authenticated') {
      settingsService.fetchRemoteSettings(request).then((remote) => {
        if (remote) {
          setSettings(remote)
          setSavedSettings(remote)
          settingsService.saveLocalSettings(remote)
        }
      })
    }
  }, [status, request])

  // Determine resolved theme
  const resolvedTheme: 'light' | 'dark' =
    settings.theme === 'system' ? (systemDark ? 'dark' : 'light') : settings.theme

  // Apply DOM attributes dynamically
  useEffect(() => {
    const root = document.documentElement

    // Theme mode
    root.setAttribute('data-theme', resolvedTheme)

    // Accent color
    let accentKey = settings.accentColor.toLowerCase()
    if (accentKey === '#16a34a') accentKey = 'emerald'
    else if (accentKey === '#2563eb') accentKey = 'blue'
    else if (accentKey === '#7c3aed') accentKey = 'purple'
    else if (accentKey === '#d97706') accentKey = 'orange'
    else if (accentKey === '#dc2626') accentKey = 'red'

    root.setAttribute('data-accent', accentKey)
    root.style.setProperty('--primary-color', settings.accentColor)

    // Density, Font Size, Animations, Glassmorphism
    root.setAttribute('data-density', settings.density)
    root.setAttribute('data-font-size', settings.fontSize)
    root.setAttribute('data-animations', settings.enableAnimations ? 'enabled' : 'disabled')
    root.setAttribute('data-glassmorphism', settings.enableGlassmorphism ? 'enabled' : 'disabled')
  }, [settings, resolvedTheme])

  const hasUnsavedChanges = JSON.stringify(settings) !== JSON.stringify(savedSettings)

  const setTheme = useCallback((theme: ThemeMode) => {
    setSettings((prev) => ({ ...prev, theme }))
  }, [])

  const setAccentColor = useCallback((accentColor: string) => {
    setSettings((prev) => ({ ...prev, accentColor }))
  }, [])

  const setDensity = useCallback((density: LayoutDensity) => {
    setSettings((prev) => ({ ...prev, density }))
  }, [])

  const setFontSize = useCallback((fontSize: FontSize) => {
    setSettings((prev) => ({ ...prev, fontSize }))
  }, [])

  const setEnableAnimations = useCallback((enableAnimations: boolean) => {
    setSettings((prev) => ({ ...prev, enableAnimations }))
  }, [])

  const setEnableGlassmorphism = useCallback((enableGlassmorphism: boolean) => {
    setSettings((prev) => ({ ...prev, enableGlassmorphism }))
  }, [])

  const setSidebarMode = useCallback((sidebarMode: SidebarMode) => {
    setSettings((prev) => ({ ...prev, sidebarMode }))
  }, [])

  const saveSettings = useCallback(async () => {
    setIsSaving(true)
    try {
      settingsService.saveLocalSettings(settings)
      if (status === 'authenticated') {
        await settingsService.updateRemoteSettings(request, settings)
      }
      setSavedSettings(settings)
    } finally {
      setIsSaving(false)
    }
  }, [settings, status, request])

  const resetSettings = useCallback(async () => {
    setIsSaving(true)
    try {
      const defaults = DEFAULT_APPEARANCE_SETTINGS
      setSettings(defaults)
      setSavedSettings(defaults)
      settingsService.saveLocalSettings(defaults)
      if (status === 'authenticated') {
        await settingsService.resetRemoteSettings(request)
      }
    } finally {
      setIsSaving(false)
    }
  }, [status, request])

  return (
    <ThemeContext.Provider
      value={{
        settings,
        savedSettings,
        resolvedTheme,
        hasUnsavedChanges,
        isSaving,
        setTheme,
        setAccentColor,
        setDensity,
        setFontSize,
        setEnableAnimations,
        setEnableGlassmorphism,
        setSidebarMode,
        saveSettings,
        resetSettings,
      }}
    >
      {children}
    </ThemeContext.Provider>
  )
}
