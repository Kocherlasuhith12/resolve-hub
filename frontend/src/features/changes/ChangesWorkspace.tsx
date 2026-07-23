import { useQuery } from '@tanstack/react-query'
import { Layers, Calendar, CheckCircle2, Clock } from 'lucide-react'
import { useAuth } from '../../auth/useAuth'

type ChangeRequest = {
  id: string
  change_number: string
  title: string
  description: string
  change_type: string
  risk_level: string
  status: string
  owner_name: string
  maintenance_window: string
  created_at: string
}

export function ChangesWorkspace({ organisationId }: { organisationId: string }) {
  const { request } = useAuth()

  const changesQuery = useQuery({
    queryKey: ['changes', organisationId],
    queryFn: () => request<ChangeRequest[]>(`/organisations/${organisationId}/changes`),
    enabled: Boolean(organisationId),
  })

  const changes = changesQuery.data ?? []
  const cabPendingCount = changes.filter((c) => c.status === 'CAB Approval').length

  return (
    <div>
      <div className="page-header-row">
        <div className="page-header">
          <h1>Change Enablement (CAB)</h1>
          <p className="page-subtitle">Change Advisory Board reviews, maintenance windows, and risk assessments</p>
        </div>
        <button className="btn-primary" type="button">
          <Layers size={16} /> Request Change (RFC)
        </button>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-card-header"><span className="kpi-card-icon amber"><Clock size={16} /></span><span className="kpi-trend neutral">Pending</span></div>
          <span className="kpi-value">{cabPendingCount}</span>
          <span className="kpi-label">CAB Review Pending</span>
        </div>
        <div className="kpi-card">
          <div className="kpi-card-header"><span className="kpi-card-icon blue"><Calendar size={16} /></span><span className="kpi-trend neutral">Scheduled</span></div>
          <span className="kpi-value">{changes.length}</span>
          <span className="kpi-label">Upcoming Window</span>
        </div>
        <div className="kpi-card">
          <div className="kpi-card-header"><span className="kpi-card-icon green"><CheckCircle2 size={16} /></span><span className="kpi-trend up">↑ 97%</span></div>
          <span className="kpi-value">97%</span>
          <span className="kpi-label">Change Success Rate</span>
        </div>
      </div>

      <div className="ticket-table-wrap">
        {changesQuery.isPending ? (
          <div className="section-message"><div className="loading-spinner" /> Loading change requests…</div>
        ) : changes.length === 0 ? (
          <div className="empty-state">
            <h3>No change requests found</h3>
            <p>Submitted RFCs and maintenance window schedules will appear here.</p>
          </div>
        ) : (
          <table className="ticket-table">
            <thead>
              <tr>
                <th>Change ID</th>
                <th>Title</th>
                <th>Type</th>
                <th>Risk Level</th>
                <th>Status</th>
                <th>Owner</th>
                <th>Maintenance Window</th>
              </tr>
            </thead>
            <tbody>
              {changes.map((c) => (
                <tr key={c.id}>
                  <td><span className="ticket-number">{c.change_number}</span></td>
                  <td><strong>{c.title}</strong></td>
                  <td>{c.change_type}</td>
                  <td>
                    <span className={`badge badge-status ${c.risk_level === 'High' ? 'priority-critical' : c.risk_level === 'Medium' ? 'priority-medium' : 'priority-low'}`}>
                      {c.risk_level} Risk
                    </span>
                  </td>
                  <td>
                    <span className={`badge badge-status ${c.status === 'Implemented' ? 'status-resolved' : c.status === 'Emergency' ? 'status-critical' : 'status-submitted'}`}>
                      {c.status}
                    </span>
                  </td>
                  <td>{c.owner_name}</td>
                  <td>
                    <span className="badge badge-status" style={{ background: 'var(--bg-page)', border: '1px solid var(--border)' }}>
                      <Calendar size={12} /> {c.maintenance_window}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
