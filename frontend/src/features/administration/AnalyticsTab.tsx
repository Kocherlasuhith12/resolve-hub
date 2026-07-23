import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../../auth/useAuth'

type AnalyticsSummary = {
  total_tickets: number
  open_tickets: number
  in_progress_tickets: number
  resolved_tickets: number
  closed_tickets: number
  tickets_by_priority: Record<string, number>
  tickets_by_category: Record<string, number>
  sla_breached_count: number
  sla_compliance_percent: number
}

export function AnalyticsTab({ organisationId }: { organisationId: string }) {
  const { request } = useAuth()

  const analytics = useQuery({
    queryKey: ['analytics-summary', organisationId],
    queryFn: () => request<AnalyticsSummary>(`/organisations/${organisationId}/analytics/summary`),
  })

  if (analytics.isPending) return <p className="section-message">Loading analytics summary…</p>
  if (analytics.isError || !analytics.data) {
    return <div className="form-error" role="alert">Analytics data could not be loaded.</div>
  }

  const data = analytics.data

  return (
    <div className="admin-panel analytics-panel" aria-labelledby="analytics-title">
      <div className="analytics-header">
        <h3 id="analytics-title">Tenant Operations Analytics</h3>
        <a
          href={`/api/v1/organisations/${organisationId}/analytics/exports/tickets`}
          download
          className="quiet-button export-button"
        >
          Export Tickets (CSV)
        </a>
      </div>

      <div className="analytics-grid">
        <div className="metric-card">
          <span className="metric-value">{data.total_tickets}</span>
          <span className="metric-label">Total Requests</span>
        </div>
        <div className="metric-card">
          <span className="metric-value">{data.open_tickets}</span>
          <span className="metric-label">Open / New</span>
        </div>
        <div className="metric-card">
          <span className="metric-value">{data.in_progress_tickets}</span>
          <span className="metric-label">In Progress</span>
        </div>
        <div className="metric-card">
          <span className="metric-value">{data.resolved_tickets}</span>
          <span className="metric-label">Resolved</span>
        </div>
        <div className="metric-card">
          <span className={`metric-value ${data.sla_compliance_percent >= 90 ? 'good' : 'warning'}`}>
            {data.sla_compliance_percent}%
          </span>
          <span className="metric-label">SLA Compliance</span>
        </div>
        <div className="metric-card">
          <span className="metric-value danger">{data.sla_breached_count}</span>
          <span className="metric-label">SLA Breached</span>
        </div>
      </div>

      <div className="analytics-breakdowns">
        <div className="breakdown-box">
          <h4>By Priority</h4>
          <ul>
            {Object.entries(data.tickets_by_priority).map(([priority, count]) => (
              <li key={priority}>
                <span>{priority}</span>
                <strong>{count}</strong>
              </li>
            ))}
          </ul>
        </div>

        <div className="breakdown-box">
          <h4>By Category</h4>
          <ul>
            {Object.entries(data.tickets_by_category).map(([category, count]) => (
              <li key={category}>
                <span>{category}</span>
                <strong>{count}</strong>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
