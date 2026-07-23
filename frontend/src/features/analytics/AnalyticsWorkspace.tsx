import { BarChart3, Clock, CheckCircle2, Shield, Smile, TrendingUp } from 'lucide-react'

export function AnalyticsWorkspace() {
  return (
    <div>
      <div className="page-header-row">
        <div className="page-header">
          <h1>Service Performance Analytics</h1>
          <p className="page-subtitle">Mean Time to Resolve (MTTR), SLA compliance, CSAT trends, and queue velocity</p>
        </div>
        <button className="btn-secondary" type="button">
          <BarChart3 size={16} /> Export Executive CSV
        </button>
      </div>

      {/* KPI Cards Grid */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-card-header"><span className="kpi-card-icon green"><Shield size={16} /></span><span className="kpi-trend up">↑ Healthy</span></div>
          <span className="kpi-value">96.8%</span>
          <span className="kpi-label">SLA Compliance Rate</span>
        </div>
        <div className="kpi-card">
          <div className="kpi-card-header"><span className="kpi-card-icon blue"><Clock size={16} /></span><span className="kpi-trend up">↓ 12m</span></div>
          <span className="kpi-value">14m</span>
          <span className="kpi-label">First Response MTTR</span>
        </div>
        <div className="kpi-card">
          <div className="kpi-card-header"><span className="kpi-card-icon green"><CheckCircle2 size={16} /></span><span className="kpi-trend up">↓ 42m</span></div>
          <span className="kpi-value">2.4h</span>
          <span className="kpi-label">Resolution MTTR</span>
        </div>
        <div className="kpi-card">
          <div className="kpi-card-header"><span className="kpi-card-icon green"><Smile size={16} /></span><span className="kpi-trend up">↑ 4.9/5</span></div>
          <span className="kpi-value">95%</span>
          <span className="kpi-label">CSAT Satisfaction</span>
        </div>
      </div>

      {/* SLA Breach Risk Visualization */}
      <div className="panel" style={{ marginBottom: 24 }}>
        <div className="panel-header">
          <h3>SLA Performance & Daily Resolution Velocity</h3>
          <span className="panel-subtitle">Past 30 days request inflow vs SLA target resolution</span>
        </div>
        <div className="chart-container">
          <svg viewBox="0 0 600 120" className="trend-chart" preserveAspectRatio="none">
            <path
              d="M0,80 Q150,30 300,50 T600,20"
              fill="none"
              stroke="var(--green-600)"
              strokeWidth="3"
            />
            <path
              d="M0,80 Q150,30 300,50 T600,20 L600,120 L0,120 Z"
              fill="url(#analytics-gradient)"
              opacity="0.12"
            />
            <defs>
              <linearGradient id="analytics-gradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--green-600)" />
                <stop offset="100%" stopColor="var(--green-600)" stopOpacity="0" />
              </linearGradient>
            </defs>
          </svg>
          <div className="chart-legend">
            <span><strong style={{ color: 'var(--green-600)' }}>—</strong> On-Time Resolution Pace</span>
            <span><strong style={{ color: 'var(--info)' }}>—</strong> SLA Target Benchmark</span>
          </div>
        </div>
      </div>

      <div className="dashboard-panels">
        <div className="panel">
          <div className="panel-header">
            <h3>Top Ticket Drivers by Service Category</h3>
          </div>
          <div className="bar-item">
            <div className="bar-item-meta"><span className="bar-item-name">VPN & Network Connectivity</span><span className="bar-item-count">64 tickets</span></div>
            <div className="bar-track"><div className="bar-fill" style={{ width: '64%' }} /></div>
          </div>
          <div className="bar-item">
            <div className="bar-item-meta"><span className="bar-item-name">Hardware & Monitor Display Setup</span><span className="bar-item-count">38 tickets</span></div>
            <div className="bar-track"><div className="bar-fill" style={{ width: '38%' }} /></div>
          </div>
          <div className="bar-item">
            <div className="bar-item-meta"><span className="bar-item-name">Identity, SSO & Access Grants</span><span className="bar-item-count">24 tickets</span></div>
            <div className="bar-track"><div className="bar-fill" style={{ width: '24%' }} /></div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <h3><TrendingUp size={16} style={{ display: 'inline', marginRight: 6 }} /> SLA Warning vs Breach Breakdown</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>On Track</span>
              <span className="badge badge-status status-resolved">96.8% (122 tickets)</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>Warning Threshold (&gt;80% time)</span>
              <span className="badge badge-status priority-medium">2.4% (3 tickets)</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>SLA Breached</span>
              <span className="badge badge-status priority-critical">0.8% (1 ticket)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
