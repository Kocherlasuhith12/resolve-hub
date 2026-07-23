import { useState, type FormEvent } from 'react'
import { Building2, Globe, ShieldAlert, Check, Trash2, Users, FileText, HardDrive, AlertTriangle } from 'lucide-react'

export function WorkspaceSettingsPage() {
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  const [confirmSlug, setConfirmSlug] = useState('')

  const [formData, setFormData] = useState({
    name: 'Northstar Operations',
    slug: 'northstar-ops',
    description: 'Core operations platform for enterprise customer support & ITSM.',
    address: '100 Tech Plaza, Suite 400, San Francisco, CA 94105',
    timezone: 'America/Los_Angeles (PST -08:00)',
    language: 'en-US (English)',
    businessHours: '09:00 - 18:00 PST',
    workingDays: 'Monday - Friday',
    region: 'us-west-2 (Oregon)',
    status: 'Active (Production)',
  })

  function handleSave(e: FormEvent) {
    e.preventDefault()
    setSuccessMsg('Workspace settings updated successfully.')
    setTimeout(() => setSuccessMsg(null), 4000)
  }

  function handleDeleteWorkspace() {
    if (confirmSlug === formData.slug) {
      alert('Workspace deletion initiated. Contact site administrator to complete process.')
      setDeleteModalOpen(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Workspace Settings</h1>
        <p className="page-subtitle">Manage organization metadata, regional parameters, business hours, and operational status</p>
      </div>

      {successMsg && (
        <div className="form-success" role="status" style={{ marginBottom: 20 }}>
          <Check size={16} style={{ display: 'inline', marginRight: 6 }} />
          {successMsg}
        </div>
      )}

      {/* Stats Header Bar */}
      <div className="kpi-grid" style={{ marginBottom: 24 }}>
        <div className="kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Workspace Members</span>
            <Users size={18} className="kpi-icon" />
          </div>
          <div className="kpi-value">24</div>
          <span className="kpi-subtitle">Active operators & admins</span>
        </div>
        <div className="kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Open Operations</span>
            <FileText size={18} className="kpi-icon" />
          </div>
          <div className="kpi-value">12</div>
          <span className="kpi-subtitle">Requests & Incidents</span>
        </div>
        <div className="kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Storage Used</span>
            <HardDrive size={18} className="kpi-icon" />
          </div>
          <div className="kpi-value">24.5 GB</div>
          <span className="kpi-subtitle">Of 100 GB tier capacity</span>
        </div>
      </div>

      <div className="dashboard-panels">
        {/* Organization Identity */}
        <div className="panel">
          <div className="panel-header">
            <h3><Building2 size={18} style={{ display: 'inline', marginRight: 6 }} /> General Information</h3>
          </div>
          <form className="compact-form" onSubmit={handleSave}>
            <label>
              <span>Workspace Name</span>
              <input
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </label>
            <label>
              <span>Workspace Slug (Unique identifier)</span>
              <input value={formData.slug} disabled readOnly style={{ opacity: 0.7 }} />
            </label>
            <label>
              <span>Company Description</span>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
              />
            </label>
            <label>
              <span>Headquarters Address</span>
              <input
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              />
            </label>
            <button className="btn-primary" type="submit" style={{ marginTop: 8 }}>
              Save General Information
            </button>
          </form>
        </div>

        {/* Regional & Working Hours */}
        <div className="panel">
          <div className="panel-header">
            <h3><Globe size={18} style={{ display: 'inline', marginRight: 6 }} /> Region & Operating Hours</h3>
          </div>
          <form className="compact-form" onSubmit={handleSave}>
            <label>
              <span>Default Time Zone</span>
              <select
                value={formData.timezone}
                onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
              >
                <option value="America/Los_Angeles (PST -08:00)">America/Los_Angeles (PST -08:00)</option>
                <option value="America/New_York (EST -05:00)">America/New_York (EST -05:00)</option>
                <option value="Europe/London (GMT +00:00)">Europe/London (GMT +00:00)</option>
                <option value="Asia/Tokyo (JST +09:00)">Asia/Tokyo (JST +09:00)</option>
              </select>
            </label>
            <label>
              <span>Default Language</span>
              <select
                value={formData.language}
                onChange={(e) => setFormData({ ...formData, language: e.target.value })}
              >
                <option value="en-US (English)">en-US (English)</option>
                <option value="es-ES (Spanish)">es-ES (Spanish)</option>
                <option value="de-DE (German)">de-DE (German)</option>
                <option value="ja-JP (Japanese)">ja-JP (Japanese)</option>
              </select>
            </label>
            <label>
              <span>Business Hours (SLA Window)</span>
              <input
                value={formData.businessHours}
                onChange={(e) => setFormData({ ...formData, businessHours: e.target.value })}
              />
            </label>
            <label>
              <span>Working Days</span>
              <input
                value={formData.workingDays}
                onChange={(e) => setFormData({ ...formData, workingDays: e.target.value })}
              />
            </label>
            <label>
              <span>Data Center Region</span>
              <input value={formData.region} disabled readOnly style={{ opacity: 0.7 }} />
            </label>
            <button className="btn-primary" type="submit" style={{ marginTop: 8 }}>
              Save Regional Settings
            </button>
          </form>
        </div>

        {/* Danger Zone */}
        <div className="panel" style={{ borderColor: 'rgba(239, 68, 68, 0.3)', gridColumn: '1 / -1' }}>
          <div className="panel-header" style={{ color: '#ef4444' }}>
            <h3><ShieldAlert size={18} style={{ display: 'inline', marginRight: 6 }} /> Danger Zone</h3>
          </div>
          <p style={{ fontSize: '0.9rem', color: '#64748b', marginBottom: 16 }}>
            Deleting a workspace is permanent and unrecoverable. All tickets, assets, knowledge articles, audit logs, and member permissions associated with <strong>{formData.slug}</strong> will be erased.
          </p>
          <button
            type="button"
            className="btn-secondary"
            style={{ borderColor: '#ef4444', color: '#ef4444' }}
            onClick={() => setDeleteModalOpen(true)}
          >
            <Trash2 size={16} style={{ display: 'inline', marginRight: 6 }} /> Delete Workspace
          </button>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {deleteModalOpen && (
        <div className="modal-backdrop" onClick={() => setDeleteModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 460 }}>
            <div className="modal-header">
              <h3 style={{ color: '#ef4444', display: 'flex', alignItems: 'center', gap: 8 }}>
                <AlertTriangle size={20} /> Delete Workspace Confirmation
              </h3>
            </div>
            <div className="modal-body" style={{ padding: '16px 0' }}>
              <p style={{ fontSize: '0.9rem', marginBottom: 12 }}>
                Please type <strong>{formData.slug}</strong> below to confirm deletion:
              </p>
              <input
                type="text"
                value={confirmSlug}
                onChange={(e) => setConfirmSlug(e.target.value)}
                placeholder={formData.slug}
                style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid #cbd5e1' }}
              />
            </div>
            <div className="modal-actions" style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
              <button className="btn-secondary" type="button" onClick={() => setDeleteModalOpen(false)}>
                Cancel
              </button>
              <button
                className="btn-primary"
                type="button"
                style={{ backgroundColor: '#ef4444', borderColor: '#ef4444' }}
                disabled={confirmSlug !== formData.slug}
                onClick={handleDeleteWorkspace}
              >
                Permanently Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
