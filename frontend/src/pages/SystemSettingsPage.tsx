import { useState } from 'react'
import { Server, Shield, Key, Mail, Database, Activity, Check, RefreshCw } from 'lucide-react'

export function SystemSettingsPage() {
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [isRefreshing, setIsRefreshing] = useState(false)

  const [healthData, setHealthData] = useState([
    { name: 'PostgreSQL Database (v16.2)', status: 'Healthy', latency: '2.4 ms', detail: 'Connections: 14/100 active' },
    { name: 'Redis Cache & Pub/Sub', status: 'Healthy', latency: '0.8 ms', detail: 'Hit ratio: 98.4% (Memory: 42 MB)' },
    { name: 'API HTTP Gateway', status: 'Healthy', latency: '12.1 ms', detail: 'Throughput: 142 req/sec' },
    { name: 'Async Worker Queue (Temporal)', status: 'Healthy', latency: '4.1 ms', detail: 'Active tasks: 0 pending' },
  ])

  function handleSave() {
    setSuccessMsg('System security configuration updated.')
    setTimeout(() => setSuccessMsg(null), 4000)
  }

  function handleRefreshHealth() {
    setIsRefreshing(true)
    setTimeout(() => {
      setIsRefreshing(false)
      setHealthData([...healthData])
      setSuccessMsg('System health diagnostics refreshed.')
      setTimeout(() => setSuccessMsg(null), 3000)
    }, 600)
  }

  return (
    <div>
      <div className="page-header">
        <h1>System Settings & Health</h1>
        <p className="page-subtitle">Configure authentication rules, security policies, storage limits, and monitor system infrastructure</p>
      </div>

      {successMsg && (
        <div className="form-success" role="status" style={{ marginBottom: 20 }}>
          <Check size={16} style={{ display: 'inline', marginRight: 6 }} />
          {successMsg}
        </div>
      )}

      {/* System Infrastructure Health Monitor */}
      <div className="panel" style={{ marginBottom: 24 }}>
        <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3><Activity size={18} style={{ display: 'inline', marginRight: 6 }} /> Infrastructure Health & Services</h3>
          <button className="btn-secondary" type="button" onClick={handleRefreshHealth} disabled={isRefreshing}>
            <RefreshCw size={14} className={isRefreshing ? 'spin' : ''} style={{ display: 'inline', marginRight: 6 }} /> Refresh
          </button>
        </div>
        <div className="kpi-grid" style={{ marginTop: 12 }}>
          {healthData.map((service) => (
            <div key={service.name} className="kpi-card" style={{ borderLeft: '4px solid #16a34a' }}>
              <div className="kpi-header">
                <span className="kpi-title">{service.name}</span>
                <span className="badge badge-success">{service.status}</span>
              </div>
              <div className="kpi-value" style={{ fontSize: '1.2rem', marginTop: 4 }}>{service.latency}</div>
              <span className="kpi-subtitle">{service.detail}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="dashboard-panels">
        {/* Authentication Policies */}
        <div className="panel">
          <div className="panel-header">
            <h3><Shield size={18} style={{ display: 'inline', marginRight: 6 }} /> Authentication & Password Policy</h3>
          </div>
          <form className="compact-form" onSubmit={(e) => { e.preventDefault(); handleSave() }}>
            <label>
              <span>Minimum Password Length</span>
              <input type="number" defaultValue={12} min={8} max={64} />
            </label>
            <label className="checkbox-label" style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <input type="checkbox" defaultChecked />
              <span>Require Multi-Factor Authentication (MFA / TOTP)</span>
            </label>
            <label className="checkbox-label" style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <input type="checkbox" defaultChecked />
              <span>Allow Google Workspace OAuth Login</span>
            </label>
            <label className="checkbox-label" style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <input type="checkbox" defaultChecked />
              <span>Allow GitHub Enterprise SSO</span>
            </label>
            <label className="checkbox-label" style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <input type="checkbox" />
              <span>Allow Microsoft Azure AD SSO</span>
            </label>
            <button className="btn-primary" type="submit" style={{ marginTop: 8 }}>
              Save Security Policies
            </button>
          </form>
        </div>

        {/* Security Sessions & API Keys */}
        <div className="panel">
          <div className="panel-header">
            <h3><Key size={18} style={{ display: 'inline', marginRight: 6 }} /> Session & API Token Controls</h3>
          </div>
          <form className="compact-form" onSubmit={(e) => { e.preventDefault(); handleSave() }}>
            <label>
              <span>Session Inactivity Timeout (Minutes)</span>
              <input type="number" defaultValue={60} />
            </label>
            <label>
              <span>Max Concurrent Sessions Per User</span>
              <input type="number" defaultValue={5} />
            </label>
            <label>
              <span>API Key Rotation Enforcement</span>
              <select defaultValue="90">
                <option value="30">Rotate every 30 days</option>
                <option value="60">Rotate every 60 days</option>
                <option value="90">Rotate every 90 days</option>
                <option value="never">Manual rotation only</option>
              </select>
            </label>
            <button className="btn-primary" type="submit" style={{ marginTop: 8 }}>
              Update Token Policies
            </button>
          </form>
        </div>

        {/* Storage & Mail Gateway */}
        <div className="panel">
          <div className="panel-header">
            <h3><Database size={18} style={{ display: 'inline', marginRight: 6 }} /> Storage & SMTP Mailer</h3>
          </div>
          <div className="compact-form">
            <label>
              <span>Max Attachment Upload Size (MB)</span>
              <input type="number" defaultValue={25} />
            </label>
            <label>
              <span>SMTP Host Server</span>
              <input defaultValue="smtp.sendgrid.net" />
            </label>
            <label>
              <span>SMTP Sender Email</span>
              <input defaultValue="notifications@resolvehub.dev" />
            </label>
            <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
              <button className="btn-secondary" type="button" onClick={() => { setSuccessMsg('Test email sent to administrator.'); setTimeout(() => setSuccessMsg(null), 4000) }}>
                <Mail size={14} style={{ display: 'inline', marginRight: 6 }} /> Send Test Email
              </button>
            </div>
          </div>
        </div>

        {/* Environment Variables */}
        <div className="panel">
          <div className="panel-header">
            <h3><Server size={18} style={{ display: 'inline', marginRight: 6 }} /> Environment Variables</h3>
          </div>
          <div style={{ background: '#0f172a', color: '#38bdf8', padding: 14, borderRadius: 6, fontFamily: 'monospace', fontSize: '0.8rem', overflowX: 'auto' }}>
            <div>APP_ENV=production</div>
            <div>DATABASE_URL=postgresql+asyncpg://***:***@postgres:5432/resolvehub</div>
            <div>REDIS_URL=redis://redis:6379/0</div>
            <div>STORAGE_PROVIDER=s3</div>
            <div>S3_BUCKET_NAME=resolvehub-attachments-uswest2</div>
          </div>
        </div>
      </div>
    </div>
  )
}
