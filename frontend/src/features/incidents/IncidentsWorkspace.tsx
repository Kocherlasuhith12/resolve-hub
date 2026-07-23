import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, Clock, ShieldAlert, Sparkles, Filter } from 'lucide-react'
import { useAuth } from '../../auth/useAuth'

type Incident = {
  id: string
  incident_number: string
  title: string
  description: string
  severity: string
  service_name: string
  status: string
  commander_name: string
  impact_summary: string
  created_at: string
}

export function IncidentsWorkspace({ organisationId }: { organisationId: string }) {
  const { request } = useAuth()
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL')

  const incidentsQuery = useQuery({
    queryKey: ['incidents', organisationId, filterSeverity],
    queryFn: () => {
      const url = filterSeverity !== 'ALL'
        ? `/organisations/${organisationId}/incidents?severity=${filterSeverity}`
        : `/organisations/${organisationId}/incidents`
      return request<Incident[]>(url)
    },
    enabled: Boolean(organisationId),
  })

  const incidents = incidentsQuery.data ?? []

  const p1Count = incidents.filter((i) => i.severity.includes('P1')).length
  const p2Count = incidents.filter((i) => i.severity.includes('P2')).length

  return (
    <div>
      {/* Page Header */}
      <div className="page-header-row">
        <div className="page-header">
          <h1>Major Incident Management</h1>
          <p className="page-subtitle">Track active P1/P2 outages, incident response command, and MTTR metrics</p>
        </div>
        <button className="btn-primary" type="button">
          <AlertTriangle size={16} /> Declare Major Incident
        </button>
      </div>

      {/* AI Incident Response Banner */}
      <div className="ai-insight-banner" style={{ borderColor: '#FECACA', background: '#FEF2F2' }}>
        <div className="ai-insight-header" style={{ color: 'var(--critical)' }}>
          <Sparkles size={16} />
          <strong>AI Incident Commander Alert</strong>
        </div>
        <p style={{ color: '#991B1B' }}>
          Anomaly detected: <strong>INC-2026-089</strong> correlates with recent payment microservice release v2.4.1. Automated rollback suggested.
        </p>
      </div>

      {/* KPI Cards Grid */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-card-header"><span className="kpi-card-icon red"><ShieldAlert size={16} /></span><span className="kpi-trend down">Active</span></div>
          <span className="kpi-value">{p1Count}</span>
          <span className="kpi-label">P1 Active Outages</span>
        </div>
        <div className="kpi-card">
          <div className="kpi-card-header"><span className="kpi-card-icon amber"><AlertTriangle size={16} /></span><span className="kpi-trend neutral">Investigating</span></div>
          <span className="kpi-value">{p2Count}</span>
          <span className="kpi-label">P2 High Severity</span>
        </div>
        <div className="kpi-card">
          <div className="kpi-card-header"><span className="kpi-card-icon blue"><Clock size={16} /></span><span className="kpi-trend up">↓ 14m</span></div>
          <span className="kpi-value">18m</span>
          <span className="kpi-label">Mean Time to Acknowledge</span>
        </div>
        <div className="kpi-card">
          <div className="kpi-card-header"><span className="kpi-card-icon green"><Clock size={16} /></span><span className="kpi-trend up">Target 45m</span></div>
          <span className="kpi-value">32m</span>
          <span className="kpi-label">Mean Time to Resolve</span>
        </div>
      </div>

      {/* Filters Toolbar */}
      <div className="ticket-toolbar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Filter size={16} style={{ color: 'var(--text-muted)' }} />
          <select className="filter-select" value={filterSeverity} onChange={(e) => setFilterSeverity(e.target.value)}>
            <option value="ALL">All Severities</option>
            <option value="P1">P1 - Critical</option>
            <option value="P2">P2 - High</option>
            <option value="P3">P3 - Moderate</option>
          </select>
        </div>
      </div>

      {/* Incident List Table */}
      <div className="ticket-table-wrap">
        {incidentsQuery.isPending ? (
          <div className="section-message"><div className="loading-spinner" /> Loading incidents…</div>
        ) : incidents.length === 0 ? (
          <div className="empty-state">
            <h3>No incidents logged</h3>
            <p>Active incidents and major outage logs will appear here.</p>
          </div>
        ) : (
          <table className="ticket-table">
            <thead>
              <tr>
                <th>Incident ID</th>
                <th>Title & Service</th>
                <th>Severity</th>
                <th>Status</th>
                <th>Commander</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {incidents.map((inc) => (
                <tr key={inc.id}>
                  <td><span className="ticket-number">{inc.incident_number}</span></td>
                  <td>
                    <h3 className="ticket-title-heading" style={{ fontSize: 14 }}>{inc.title}</h3>
                    <p style={{ margin: '2px 0 0', fontSize: 12, color: 'var(--text-muted)' }}>
                      Service: <strong>{inc.service_name}</strong> — {inc.impact_summary}
                    </p>
                  </td>
                  <td>
                    <span className={`badge badge-status ${inc.severity.startsWith('P1') ? 'priority-critical' : inc.severity.startsWith('P2') ? 'priority-high' : 'priority-medium'}`}>
                      {inc.severity}
                    </span>
                  </td>
                  <td>
                    <span className={`badge badge-status ${inc.status === 'Resolved' ? 'status-resolved' : inc.status === 'Investigating' ? 'status-critical' : 'status-assigned'}`}>
                      <span className="badge-dot" />
                      {inc.status}
                    </span>
                  </td>
                  <td>{inc.commander_name}</td>
                  <td>
                    <time dateTime={inc.created_at}>
                      {new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(inc.created_at))}
                    </time>
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
