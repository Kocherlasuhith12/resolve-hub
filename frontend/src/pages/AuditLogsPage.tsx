import { useState } from 'react'
import { Download, Search, Calendar } from 'lucide-react'

export function AuditLogsPage() {
  const [searchTerm, setSearchTerm] = useState('')

  const logs = [
    {
      id: 'AUD-901',
      actor: 'Admin User',
      email: 'admin@resolvehub.dev',
      action: 'WORKSPACE_SETTINGS_UPDATED',
      target: 'Northstar Operations',
      ip: '192.168.1.45',
      time: '2026-07-22 11:20:04 UTC',
      status: 'SUCCESS',
    },
    {
      id: 'AUD-902',
      actor: 'Sarah Connor',
      email: 'sarah@resolvehub.dev',
      action: 'ROLE_PERMISSIONS_CHANGED',
      target: 'Role: Senior Operator',
      ip: '192.168.1.88',
      time: '2026-07-22 10:45:12 UTC',
      status: 'SUCCESS',
    },
    {
      id: 'AUD-903',
      actor: 'Alex Rivera',
      email: 'alex@resolvehub.dev',
      action: 'USER_LOGIN_SUCCESS',
      target: 'Session Auth (JWT)',
      ip: '10.0.4.12',
      time: '2026-07-22 09:15:30 UTC',
      status: 'SUCCESS',
    },
    {
      id: 'AUD-904',
      actor: 'System Bot',
      email: 'system@resolvehub.dev',
      action: 'KNOWLEDGE_ARTICLE_PUBLISHED',
      target: 'KB-802',
      ip: '127.0.0.1',
      time: '2026-07-21 18:30:00 UTC',
      status: 'SUCCESS',
    },
    {
      id: 'AUD-905',
      actor: 'External Guest',
      email: 'unknown@external.com',
      action: 'FAILED_LOGIN_ATTEMPT',
      target: 'Auth Endpoint',
      ip: '198.51.100.42',
      time: '2026-07-21 14:12:00 UTC',
      status: 'DENIED',
    },
  ]

  const filteredLogs = logs.filter(
    (log) =>
      log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.actor.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.target.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1>Administrator Audit Trail & Compliance</h1>
          <p className="page-subtitle">Immutable log of workspace security events, authentication attempts, role updates, and system changes</p>
        </div>
        <button
          className="btn-secondary"
          type="button"
          onClick={() => alert('Exporting audit log CSV...')}
          style={{ display: 'flex', alignItems: 'center', gap: 6 }}
        >
          <Download size={16} /> Export CSV
        </button>
      </div>

      {/* Search & Date Range Controls */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        <div style={{ position: 'relative', flex: 1, minWidth: 260 }}>
          <Search size={16} style={{ position: 'absolute', left: 10, top: 10, color: '#94a3b8' }} />
          <input
            type="search"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by action, user, or IP address..."
            style={{ width: '100%', paddingLeft: 34, height: 36, borderRadius: 6, border: '1px solid #cbd5e1' }}
          />
        </div>
        <button className="btn-secondary" type="button" style={{ display: 'flex', alignItems: 'center', gap: 6, height: 36 }}>
          <Calendar size={14} /> Date Range
        </button>
      </div>

      {/* Audit Log Table */}
      <div className="panel" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="tickets-table">
          <thead>
            <tr>
              <th>Log ID</th>
              <th>Actor</th>
              <th>Action Event</th>
              <th>Target Resource</th>
              <th>IP Address</th>
              <th>Timestamp</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {filteredLogs.map((log) => (
              <tr key={log.id}>
                <td style={{ fontWeight: 600, fontSize: '0.8rem', fontFamily: 'monospace' }}>{log.id}</td>
                <td>
                  <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{log.actor}</div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{log.email}</div>
                </td>
                <td>
                  <span style={{ fontFamily: 'monospace', fontSize: '0.8rem', background: '#f1f5f9', padding: '2px 6px', borderRadius: 4 }}>
                    {log.action}
                  </span>
                </td>
                <td>{log.target}</td>
                <td style={{ fontFamily: 'monospace', fontSize: '0.8rem', color: '#64748b' }}>{log.ip}</td>
                <td style={{ fontSize: '0.8rem', color: '#64748b' }}>{log.time}</td>
                <td>
                  <span className={`badge ${log.status === 'SUCCESS' ? 'badge-success' : 'badge-danger'}`}>
                    {log.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
