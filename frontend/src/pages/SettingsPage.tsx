import { useState, type FormEvent } from 'react'
import { Settings, Shield, Check } from 'lucide-react'

export function SettingsPage() {
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  function handleSave(e: FormEvent) {
    e.preventDefault()
    setSuccessMsg('Workspace settings saved.')
    setTimeout(() => setSuccessMsg(null), 4000)
  }

  return (
    <div>
      <div className="page-header">
        <h1>Workspace Settings & Preferences</h1>
        <p className="page-subtitle">Configure organization branding, default SLAs, notifications, and security policies</p>
      </div>

      {successMsg && (
        <div className="form-success" role="status" style={{ marginBottom: 20 }}>
          <Check size={16} style={{ display: 'inline', marginRight: 6 }} />
          {successMsg}
        </div>
      )}

      <div className="dashboard-panels">
        {/* Workspace Branding */}
        <div className="panel">
          <div className="panel-header">
            <h3><Settings size={16} style={{ display: 'inline', marginRight: 6 }} /> General & Branding</h3>
          </div>
          <form className="compact-form" onSubmit={handleSave}>
            <label>
              <span>Workspace Name</span>
              <input defaultValue="Northstar Operations" required />
            </label>
            <label>
              <span>Workspace Slug</span>
              <input defaultValue="northstar-operations" disabled readOnly />
            </label>
            <label>
              <span>Primary Accent Color</span>
              <select defaultValue="#16A34A">
                <option value="#16A34A">Emerald Green (#16A34A)</option>
                <option value="#2563EB">Royal Blue (#2563EB)</option>
                <option value="#7C3AED">Deep Purple (#7C3AED)</option>
              </select>
            </label>
            <button className="btn-primary" type="submit">Save Workspace Settings</button>
          </form>
        </div>

        {/* Security & Access Policies */}
        <div className="panel">
          <div className="panel-header">
            <h3><Shield size={16} style={{ display: 'inline', marginRight: 6 }} /> Security & Multi-Tenancy</h3>
          </div>
          <div className="compact-form">
            <label className="checkbox-label" style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <input type="checkbox" defaultChecked />
              <span>Enforce Row Level Security (RLS) on all tenant tables</span>
            </label>
            <label className="checkbox-label" style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <input type="checkbox" defaultChecked />
              <span>Require SSO / MFA for all Administrator roles</span>
            </label>
            <label className="checkbox-label" style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <input type="checkbox" defaultChecked />
              <span>Sanitize ticket body & attachments against malware</span>
            </label>
            <button className="btn-secondary" type="button" onClick={() => { setSuccessMsg('Security policy enforced.'); setTimeout(() => setSuccessMsg(null), 4000) }}>
              Enforce Security Policies
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
