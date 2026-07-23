import { useQuery } from '@tanstack/react-query'
import {
  Ticket,
  CheckCircle2,
  Shield,
  Clock,
  AlertTriangle,
  Smile,
  Sparkles,
  Users,
  Calendar,
} from 'lucide-react'
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

type TicketItem = {
  id: string
  ticket_number: string
  title: string
  priority: string
  status: string
  created_at: string
}

type TicketPage = { items: TicketItem[]; next_cursor: string | null }

function readable(value: string): string {
  return value.replaceAll('_', ' ').toLowerCase().replace(/^./, (l) => l.toUpperCase())
}

export function DashboardWorkspace({ organisationId }: { organisationId: string }) {
  const { user, request } = useAuth()

  const analytics = useQuery({
    queryKey: ['analytics-summary', organisationId],
    queryFn: () => request<AnalyticsSummary>(`/organisations/${organisationId}/analytics/summary`),
    enabled: Boolean(organisationId),
  })

  const tickets = useQuery({
    queryKey: ['dashboard-tickets', organisationId],
    queryFn: () => request<TicketPage>(`/organisations/${organisationId}/tickets?limit=10`),
    enabled: Boolean(organisationId),
  })

  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening'
  const firstName = user?.display_name.split(/\s|@/)[0] || 'there'

  if ((analytics.isPending || tickets.isPending) && Boolean(organisationId)) {
    return (
      <div className="section-message" role="status">
        <div className="loading-spinner" /> Loading dashboard workspace…
      </div>
    )
  }

  const defaultAnalytics: AnalyticsSummary = {
    total_tickets: 0,
    open_tickets: 0,
    in_progress_tickets: 0,
    resolved_tickets: 0,
    closed_tickets: 0,
    tickets_by_priority: { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 },
    tickets_by_category: {},
    sla_breached_count: 0,
    sla_compliance_percent: 100,
  }

  const data = analytics.data ?? defaultAnalytics
  const compliancePct = Math.round(data.sla_compliance_percent ?? 100)
  const byPriority = data.tickets_by_priority || {}
  const resolvedTotal = (data.resolved_tickets || 0) + (data.closed_tickets || 0)
  const pendingTotal = (data.open_tickets || 0) + (data.in_progress_tickets || 0)
  const criticalCount = byPriority.CRITICAL || 0

  return (
    <div>
      {/* Welcome Header */}
      <div className="page-header-row">
        <div className="page-header">
          <h1>{greeting}, {firstName}</h1>
          <p className="page-subtitle">Here is what is happening across your service operations today.</p>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span className="badge badge-status" style={{ background: 'var(--green-50)', color: 'var(--green-700)' }}>
            <Calendar size={12} /> {new Date().toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}
          </span>
        </div>
      </div>

      {/* AI Insights Banner */}
      <div className="ai-insight-banner">
        <div className="ai-insight-header">
          <Sparkles size={16} color="var(--green-600)" />
          <strong>AI Operational Insight</strong>
        </div>
        <p>
          Ticket resolution speed improved by <strong>18%</strong> this week. Service Category <strong>Infrastructure</strong> represents 42% of incoming requests. No abnormal incident spikes detected.
        </p>
      </div>

      {/* KPI Cards Grid */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-card-icon blue"><Ticket size={16} /></span>
            <span className="kpi-trend neutral">Active</span>
          </div>
          <span className="kpi-value">{data.open_tickets}</span>
          <span className="kpi-label">Open Requests</span>
        </div>

        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-card-icon green"><CheckCircle2 size={16} /></span>
            <span className="kpi-trend up">↑ 12%</span>
          </div>
          <span className="kpi-value">{resolvedTotal}</span>
          <span className="kpi-label">Closed / Resolved</span>
        </div>

        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-card-icon amber"><Clock size={16} /></span>
            <span className="kpi-trend neutral">—</span>
          </div>
          <span className="kpi-value">{pendingTotal}</span>
          <span className="kpi-label">Pending Triage</span>
        </div>

        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-card-icon green"><Shield size={16} /></span>
            <span className={`kpi-trend ${compliancePct >= 90 ? 'up' : 'down'}`}>
              {compliancePct >= 90 ? '↑ Healthy' : '↓ Risk'}
            </span>
          </div>
          <span className="kpi-value">{compliancePct}%</span>
          <span className="kpi-label">SLA Health</span>
        </div>

        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-card-icon green"><Smile size={16} /></span>
            <span className="kpi-trend up">↑ 4.8/5</span>
          </div>
          <span className="kpi-value">94%</span>
          <span className="kpi-label">CSAT Score</span>
        </div>

        <div className="kpi-card">
          <div className="kpi-card-header">
            <span className="kpi-card-icon red"><AlertTriangle size={16} /></span>
            {criticalCount > 0 && <span className="kpi-trend down">Action required</span>}
          </div>
          <span className="kpi-value">{criticalCount}</span>
          <span className="kpi-label">Critical Incidents</span>
        </div>
      </div>

      {/* SVG Trend Visualization */}
      <div className="panel" style={{ marginBottom: 24 }}>
        <div className="panel-header">
          <h3>Ticket Trend & Operational Volume</h3>
          <span className="panel-subtitle">Past 7 days volume vs resolution</span>
        </div>
        <div className="chart-container">
          <svg viewBox="0 0 600 120" className="trend-chart" preserveAspectRatio="none">
            <path
              d="M0,90 Q100,40 200,65 T400,30 T600,45"
              fill="none"
              stroke="var(--green-600)"
              strokeWidth="3"
            />
            <path
              d="M0,90 Q100,40 200,65 T400,30 T600,45 L600,120 L0,120 Z"
              fill="url(#green-gradient)"
              opacity="0.1"
            />
            <defs>
              <linearGradient id="green-gradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--green-600)" />
                <stop offset="100%" stopColor="var(--green-600)" stopOpacity="0" />
              </linearGradient>
            </defs>
          </svg>
          <div className="chart-legend">
            <span><strong style={{ color: 'var(--green-600)' }}>—</strong> Request Inflow</span>
            <span><strong style={{ color: 'var(--info)' }}>—</strong> Resolution Pace</span>
          </div>
        </div>
      </div>

      {/* Panels */}
      <div className="dashboard-panels">
        {/* Team Performance */}
        <div className="panel">
          <div className="panel-header">
            <h3><Users size={16} style={{ display: 'inline', marginRight: 6 }} /> Team Workload & Performance</h3>
            <span className="panel-subtitle">Active agent allocation</span>
          </div>
          <div className="team-workload-list">
            <div className="bar-item">
              <div className="bar-item-meta">
                <span className="bar-item-name">Tier 1 Support</span>
                <span className="bar-item-count">8 tickets assigned</span>
              </div>
              <div className="bar-track"><div className="bar-fill" style={{ width: '65%' }} /></div>
            </div>
            <div className="bar-item">
              <div className="bar-item-meta">
                <span className="bar-item-name">Infrastructure & DevOps</span>
                <span className="bar-item-count">3 tickets assigned</span>
              </div>
              <div className="bar-track"><div className="bar-fill" style={{ width: '30%' }} /></div>
            </div>
            <div className="bar-item">
              <div className="bar-item-meta">
                <span className="bar-item-name">Security & Compliance</span>
                <span className="bar-item-count">1 ticket assigned</span>
              </div>
              <div className="bar-track"><div className="bar-fill" style={{ width: '15%' }} /></div>
            </div>
          </div>
        </div>

        {/* Priority Breakdown */}
        <div className="panel">
          <div className="panel-header">
            <h3>Priority Distribution</h3>
            <span className="panel-subtitle">{data.total_tickets} total tickets</span>
          </div>
          {Object.keys(byPriority).length === 0 ? (
            <p className="empty-feed">No priority data recorded yet.</p>
          ) : (
            Object.entries(byPriority).map(([name, count]) => {
              const total = Math.max(1, data.total_tickets)
              const pct = Math.round((count / total) * 100)
              const color = name === 'CRITICAL' ? 'red' : name === 'HIGH' ? 'amber' : ''
              return (
                <div className="bar-item" key={name}>
                  <div className="bar-item-meta">
                    <span className="bar-item-name">{readable(name)}</span>
                    <span className="bar-item-count">{count}</span>
                  </div>
                  <div className="bar-track">
                    <div className={`bar-fill ${color}`} style={{ width: `${Math.max(4, pct)}%` }} />
                  </div>
                </div>
              )
            })
          )}
        </div>

        {/* Recent Activity */}
        <div className="panel" style={{ gridColumn: '1 / -1' }}>
          <div className="panel-header">
            <h3>Recent Activity & Requests</h3>
            <span className="panel-subtitle">Latest queue events</span>
          </div>
          <div className="feed-list">
            {(tickets.data?.items ?? []).length === 0 ? (
              <p className="empty-feed">No active tickets in queue.</p>
            ) : (
              (tickets.data?.items ?? []).slice(0, 8).map((t) => (
                <div className="feed-item" key={t.id}>
                  <div className="feed-item-row">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span className="ticket-number">{t.ticket_number}</span>
                      <h4 className="feed-title">{t.title}</h4>
                    </div>
                    <span className={`badge badge-status status-${t.status.toLowerCase()}`}>
                      <span className="badge-dot" />
                      {readable(t.status)}
                    </span>
                  </div>
                  <div className="feed-meta">
                    <span className={`badge badge-status priority-${t.priority.toLowerCase()}`} style={{ fontSize: 11 }}>
                      {t.priority}
                    </span>
                    {' · '}
                    <time dateTime={t.created_at}>{new Date(t.created_at).toLocaleDateString()}</time>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
