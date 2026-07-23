import { useState, type FormEvent } from 'react'
import { useAuth } from '../auth/useAuth'
import { User, Shield, Laptop, Check } from 'lucide-react'

export function ProfilePage() {
  const { user } = useAuth()
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  const initials = (user?.display_name || user?.email || '?')
    .split(/\s|@/)
    .slice(0, 2)
    .map((s) => s[0]?.toUpperCase() || '')
    .join('')

  function handleSave(e: FormEvent) {
    e.preventDefault()
    setSuccessMsg('Profile information updated successfully.')
    setTimeout(() => setSuccessMsg(null), 4000)
  }

  return (
    <div>
      <div className="page-header">
        <h1>User Profile & Settings</h1>
        <p className="page-subtitle">Manage personal account details, security credentials, and active sessions</p>
      </div>

      {successMsg && (
        <div className="form-success" role="status" style={{ marginBottom: 20 }}>
          <Check size={16} style={{ display: 'inline', marginRight: 6 }} />
          {successMsg}
        </div>
      )}

      <div className="dashboard-panels">
        {/* Profile Details Card */}
        <div className="panel">
          <div className="panel-header">
            <h3><User size={16} style={{ display: 'inline', marginRight: 6 }} /> Account Details</h3>
          </div>
          <form className="compact-form" onSubmit={handleSave}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
              <span className="profile-avatar" style={{ width: 48, height: 48, fontSize: 18 }}>{initials}</span>
              <div>
                <strong>{user?.display_name}</strong>
                <p style={{ margin: 0, fontSize: 12, color: 'var(--text-muted)' }}>{user?.email}</p>
              </div>
            </div>
            <label>
              <span>Full Display Name</span>
              <input defaultValue={user?.display_name} required />
            </label>
            <label>
              <span>Email Address</span>
              <input defaultValue={user?.email} disabled readOnly />
              <small>Verified corporate email</small>
            </label>
            <button className="btn-primary" type="submit">Save Changes</button>
          </form>
        </div>

        {/* Security & Password */}
        <div className="panel">
          <div className="panel-header">
            <h3><Shield size={16} style={{ display: 'inline', marginRight: 6 }} /> Security & Password</h3>
          </div>
          <form className="compact-form" onSubmit={handleSave}>
            <label>
              <span>Current Password</span>
              <input type="password" placeholder="••••••••••••" />
            </label>
            <label>
              <span>New Password</span>
              <input type="password" placeholder="Min 12 characters" />
            </label>
            <button className="btn-secondary" type="submit">Update Password</button>
          </form>

          <hr className="kb-divider" style={{ margin: '20px 0' }} />

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <strong>Two-Factor Authentication (2FA)</strong>
                <p style={{ margin: 0, fontSize: 12, color: 'var(--text-muted)' }}>Authenticator app / Security Key</p>
              </div>
              <span className="badge badge-status status-resolved">Enabled</span>
            </div>
          </div>
        </div>

        {/* Active Browser Sessions */}
        <div className="panel" style={{ gridColumn: '1 / -1' }}>
          <div className="panel-header">
            <h3><Laptop size={16} style={{ display: 'inline', marginRight: 6 }} /> Active Sessions</h3>
            <span className="panel-subtitle">Rotating session tokens with auto-revocation</span>
          </div>
          <div className="feed-list">
            <div className="feed-item">
              <div className="feed-item-row">
                <div>
                  <strong>macOS (Chrome 122) — Current Device</strong>
                  <p style={{ margin: '2px 0 0', fontSize: 12, color: 'var(--text-muted)' }}>IP: 192.168.1.1 · San Francisco, US</p>
                </div>
                <span className="badge badge-status status-resolved">Active Session</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
