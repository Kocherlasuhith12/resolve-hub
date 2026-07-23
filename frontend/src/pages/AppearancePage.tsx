import { useState } from 'react'
import {
  Sun,
  Moon,
  Laptop,
  Palette,
  Layout,
  Type,
  Check,
  RotateCcw,
  AlertCircle,
  Sparkles,
} from 'lucide-react'
import { useTheme } from '../theme/ThemeContext'

export function AppearancePage() {
  const {
    settings,
    hasUnsavedChanges,
    isSaving,
    setTheme,
    setAccentColor,
    setDensity,
    setFontSize,
    setEnableAnimations,
    setEnableGlassmorphism,
    saveSettings,
    resetSettings,
  } = useTheme()

  const [toastMsg, setToastMsg] = useState<string | null>(null)
  const [resetModalOpen, setResetModalOpen] = useState(false)

  const accentOptions = [
    { name: 'Emerald Green', hex: '#16A34A' },
    { name: 'Royal Blue', hex: '#2563EB' },
    { name: 'Deep Purple', hex: '#7C3AED' },
    { name: 'Amber Orange', hex: '#D97706' },
    { name: 'Crimson Red', hex: '#DC2626' },
  ]

  async function handleSave() {
    await saveSettings()
    setToastMsg('Theme settings saved and synchronized successfully.')
    setTimeout(() => setToastMsg(null), 4000)
  }

  async function handleConfirmReset() {
    await resetSettings()
    setResetModalOpen(false)
    setToastMsg('Layout and appearance settings reset to system defaults.')
    setTimeout(() => setToastMsg(null), 4000)
  }

  return (
    <div>
      <div className="page-header">
        <h1>Appearance & Theme</h1>
        <p className="page-subtitle">
          Customize theme modes, color accents, typography scale, layout density, and interface motion controls globally across ResolveHub
        </p>
      </div>

      {/* Unsaved Changes Banner */}
      {hasUnsavedChanges && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'rgba(217, 119, 6, 0.12)',
            border: '1px solid #d97706',
            color: '#b45309',
            padding: '12px 16px',
            borderRadius: 8,
            marginBottom: 20,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 600, fontSize: '0.9rem' }}>
            <AlertCircle size={18} /> You have unsaved theme changes.
          </div>
          <button className="btn-primary" type="button" onClick={handleSave} disabled={isSaving} style={{ backgroundColor: '#d97706', borderColor: '#d97706' }}>
            {isSaving ? 'Saving...' : 'Save Theme Layout'}
          </button>
        </div>
      )}

      {/* Action Toast Notification */}
      {toastMsg && (
        <div className="form-success" role="status" style={{ marginBottom: 20 }}>
          <Check size={16} style={{ display: 'inline', marginRight: 6 }} />
          {toastMsg}
        </div>
      )}

      <div className="dashboard-panels">
        {/* Theme Mode */}
        <div className="panel">
          <div className="panel-header">
            <h3><Sun size={18} style={{ display: 'inline', marginRight: 6 }} /> Application Theme Mode</h3>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginTop: 12 }}>
            <button
              type="button"
              className={`theme-card-btn ${settings.theme === 'light' ? 'active' : ''}`}
              onClick={() => setTheme('light')}
              style={{
                border: settings.theme === 'light' ? `2px solid ${settings.accentColor}` : '1px solid var(--border)',
                padding: 16,
                borderRadius: 8,
                background: 'var(--bg-card)',
                color: 'var(--text-primary)',
                cursor: 'pointer',
                textAlign: 'center',
                boxShadow: settings.theme === 'light' ? '0 0 0 1px var(--green-primary)' : 'none',
              }}
            >
              <Sun size={24} style={{ marginBottom: 8, color: '#d97706' }} />
              <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>Light</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>High contrast light surfaces</div>
            </button>

            <button
              type="button"
              className={`theme-card-btn ${settings.theme === 'dark' ? 'active' : ''}`}
              onClick={() => setTheme('dark')}
              style={{
                border: settings.theme === 'dark' ? `2px solid ${settings.accentColor}` : '1px solid var(--border)',
                padding: 16,
                borderRadius: 8,
                background: '#0f172a',
                color: '#f8fafc',
                cursor: 'pointer',
                textAlign: 'center',
                boxShadow: settings.theme === 'dark' ? '0 0 0 1px var(--green-primary)' : 'none',
              }}
            >
              <Moon size={24} style={{ marginBottom: 8, color: '#38bdf8' }} />
              <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>Dark</div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Sleek low light workspace</div>
            </button>

            <button
              type="button"
              className={`theme-card-btn ${settings.theme === 'system' ? 'active' : ''}`}
              onClick={() => setTheme('system')}
              style={{
                border: settings.theme === 'system' ? `2px solid ${settings.accentColor}` : '1px solid var(--border)',
                padding: 16,
                borderRadius: 8,
                background: 'var(--bg-muted)',
                color: 'var(--text-primary)',
                cursor: 'pointer',
                textAlign: 'center',
                boxShadow: settings.theme === 'system' ? '0 0 0 1px var(--green-primary)' : 'none',
              }}
            >
              <Laptop size={24} style={{ marginBottom: 8, color: 'var(--text-secondary)' }} />
              <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>System</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Automatically sync with OS</div>
            </button>
          </div>
        </div>

        {/* Accent Color Palette */}
        <div className="panel">
          <div className="panel-header">
            <h3><Palette size={18} style={{ display: 'inline', marginRight: 6 }} /> Accent Color Palette</h3>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 14 }}>
            Selecting an accent color immediately updates buttons, active links, focus rings, badges, and progress bars.
          </p>
          <div style={{ display: 'flex', gap: 14, alignItems: 'center', flexWrap: 'wrap' }}>
            {accentOptions.map((opt) => (
              <button
                key={opt.hex}
                type="button"
                onClick={() => setAccentColor(opt.hex)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '8px 14px',
                  borderRadius: 20,
                  border: settings.accentColor.toLowerCase() === opt.hex.toLowerCase() ? `2px solid ${opt.hex}` : '1px solid var(--border)',
                  background: settings.accentColor.toLowerCase() === opt.hex.toLowerCase() ? `${opt.hex}18` : 'var(--bg-card)',
                  color: 'var(--text-primary)',
                  cursor: 'pointer',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                }}
              >
                <span
                  style={{
                    width: 14,
                    height: 14,
                    borderRadius: '50%',
                    background: opt.hex,
                    display: 'inline-block',
                  }}
                />
                {opt.name}
              </button>
            ))}
          </div>
        </div>

        {/* Layout Density */}
        <div className="panel">
          <div className="panel-header">
            <h3><Layout size={18} style={{ display: 'inline', marginRight: 6 }} /> Layout Density</h3>
          </div>
          <div className="compact-form">
            <label>
              <span>Density Mode</span>
              <select
                value={settings.density}
                onChange={(e) => setDensity(e.target.value as 'compact' | 'comfortable' | 'spacious')}
              >
                <option value="compact">Compact (Tighter padding & higher data density)</option>
                <option value="comfortable">Comfortable (Standard enterprise spacing)</option>
                <option value="spacious">Spacious (Relaxed padding & breathing room)</option>
              </select>
            </label>
          </div>
        </div>

        {/* Font Sizing */}
        <div className="panel">
          <div className="panel-header">
            <h3><Type size={18} style={{ display: 'inline', marginRight: 6 }} /> Font Scale</h3>
          </div>
          <div className="compact-form">
            <label>
              <span>Global Typography Scale</span>
              <select
                value={settings.fontSize}
                onChange={(e) => setFontSize(e.target.value as 'small' | 'medium' | 'large')}
              >
                <option value="small">Small (13px body)</option>
                <option value="medium">Medium (14px standard)</option>
                <option value="large">Large (16px accessible font)</option>
              </select>
            </label>
          </div>
        </div>

        {/* Motion & Glassmorphism Controls */}
        <div className="panel" style={{ gridColumn: '1 / -1' }}>
          <div className="panel-header">
            <h3><Sparkles size={18} style={{ display: 'inline', marginRight: 6 }} /> Interface Behavior & Visual Effects</h3>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16, marginTop: 8 }}>
            <label className="checkbox-label" style={{ display: 'flex', gap: 12, alignItems: 'flex-start', padding: 12, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg-card)' }}>
              <input
                type="checkbox"
                checked={settings.enableAnimations}
                onChange={(e) => setEnableAnimations(e.target.checked)}
                style={{ marginTop: 3 }}
              />
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>Enable Motion & Micro-animations</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Allows smooth page transitions, hover states, and keyframe animations</div>
              </div>
            </label>

            <label className="checkbox-label" style={{ display: 'flex', gap: 12, alignItems: 'flex-start', padding: 12, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg-card)' }}>
              <input
                type="checkbox"
                checked={settings.enableGlassmorphism}
                onChange={(e) => setEnableGlassmorphism(e.target.checked)}
                style={{ marginTop: 3 }}
              />
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>Enable Glassmorphism Blur</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Applies backdrop filter blur on navbars, sidebars, and dialog containers</div>
              </div>
            </label>
          </div>
        </div>
      </div>

      {/* Control Buttons */}
      <div style={{ display: 'flex', gap: 12, marginTop: 24 }}>
        <button className="btn-primary" type="button" onClick={handleSave} disabled={isSaving}>
          <Check size={16} style={{ display: 'inline', marginRight: 6 }} />
          {isSaving ? 'Saving Theme...' : 'Save Theme Layout'}
        </button>
        <button className="btn-secondary" type="button" onClick={() => setResetModalOpen(true)}>
          <RotateCcw size={16} style={{ display: 'inline', marginRight: 6 }} /> Reset Layout Defaults
        </button>
      </div>

      {/* Reset Confirmation Modal */}
      {resetModalOpen && (
        <div className="modal-backdrop" onClick={() => setResetModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 440 }}>
            <div className="modal-header">
              <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <RotateCcw size={18} /> Reset Layout Defaults
              </h3>
            </div>
            <div className="modal-body" style={{ padding: '16px 0' }}>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                Are you sure you want to restore theme mode, accent color, font scale, layout density, and animation preferences to default system values?
              </p>
            </div>
            <div className="modal-actions" style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
              <button className="btn-secondary" type="button" onClick={() => setResetModalOpen(false)}>
                Cancel
              </button>
              <button className="btn-primary" type="button" onClick={handleConfirmReset}>
                Reset to Defaults
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
