import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { FileCode, Search, CheckCircle2, AlertTriangle, Sparkles } from 'lucide-react'
import { useAuth } from '../../auth/useAuth'

type Problem = {
  id: string
  problem_number: string
  title: string
  category: string
  status: string
  root_cause: string
  workaround: string
  impacted_incidents_count: number
  created_at: string
}

export function ProblemsWorkspace({ organisationId }: { organisationId: string }) {
  const { request } = useAuth()
  const [search, setSearch] = useState('')

  const problemsQuery = useQuery({
    queryKey: ['problems', organisationId, search],
    queryFn: () => {
      const url = search.trim()
        ? `/organisations/${organisationId}/problems?search=${encodeURIComponent(search.trim())}`
        : `/organisations/${organisationId}/problems`
      return request<Problem[]>(url)
    },
    enabled: Boolean(organisationId),
  })

  const problems = problemsQuery.data ?? []

  return (
    <div>
      <div className="page-header-row">
        <div className="page-header">
          <h1>Problem & RCA Management</h1>
          <p className="page-subtitle">Root Cause Analysis (RCA), Known Errors Database (KEDB), and permanent fixes</p>
        </div>
        <button className="btn-primary" type="button">
          <FileCode size={16} /> Log Problem Record
        </button>
      </div>

      <div className="ai-insight-banner">
        <div className="ai-insight-header">
          <Sparkles size={16} color="var(--green-600)" />
          <strong>AI Known Error Matching Active</strong>
        </div>
        <p>Incoming tickets auto-matched against Known Error Database (KEDB). Workarounds auto-suggested to agents.</p>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-card-header"><span className="kpi-card-icon amber"><FileCode size={16} /></span><span className="kpi-trend neutral">Active</span></div>
          <span className="kpi-value">{problems.length}</span>
          <span className="kpi-label">Open Problems</span>
        </div>
        <div className="kpi-card">
          <div className="kpi-card-header"><span className="kpi-card-icon blue"><AlertTriangle size={16} /></span><span className="kpi-trend neutral">KEDB</span></div>
          <span className="kpi-value">14</span>
          <span className="kpi-label">Known Errors</span>
        </div>
        <div className="kpi-card">
          <div className="kpi-card-header"><span className="kpi-card-icon green"><CheckCircle2 size={16} /></span><span className="kpi-trend up">↑ 88%</span></div>
          <span className="kpi-value">88%</span>
          <span className="kpi-label">RCA SLA Compliance</span>
        </div>
      </div>

      <div className="ticket-toolbar">
        <div style={{ display: 'flex', gap: 8, flex: 1, alignItems: 'center' }}>
          <Search size={16} style={{ color: 'var(--text-muted)' }} />
          <input
            className="ticket-search-input"
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search problem records, root causes, workarounds…"
          />
        </div>
      </div>

      <div className="ticket-table-wrap">
        {problemsQuery.isPending ? (
          <div className="section-message"><div className="loading-spinner" /> Loading problem records…</div>
        ) : problems.length === 0 ? (
          <div className="empty-state">
            <h3>No problem records found</h3>
            <p>Logged RCA records and known errors will appear here.</p>
          </div>
        ) : (
          <table className="ticket-table">
            <thead>
              <tr>
                <th>Problem ID</th>
                <th>Title & Root Cause</th>
                <th>Status</th>
                <th>Workaround</th>
                <th>Related Incidents</th>
              </tr>
            </thead>
            <tbody>
              {problems.map((p) => (
                <tr key={p.id}>
                  <td><span className="ticket-number">{p.problem_number}</span></td>
                  <td>
                    <h3 className="ticket-title-heading" style={{ fontSize: 14 }}>{p.title}</h3>
                    <p style={{ margin: '4px 0 0', fontSize: 12, color: 'var(--text-secondary)' }}>
                      <strong>RCA:</strong> {p.root_cause || 'Investigation in progress'}
                    </p>
                  </td>
                  <td>
                    <span className={`badge badge-status ${p.status === 'Investigation' ? 'status-submitted' : p.status === 'RCA Complete' ? 'status-assigned' : 'status-resolved'}`}>
                      {p.status}
                    </span>
                  </td>
                  <td style={{ fontSize: 13, maxWidth: 300 }}>{p.workaround || 'None specified'}</td>
                  <td><span className="badge badge-status priority-high">{p.impacted_incidents_count} incidents</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
