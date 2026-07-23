import { useState } from 'react'
import { Activity, MessageSquare, CheckCircle, UserPlus, Sparkles, Filter, Clock } from 'lucide-react'

export function ActivityPage() {
  const [filterRange, setFilterRange] = useState('all')
  const [filterType, setFilterType] = useState('all')

  const activities = [
    {
      id: 'act-1',
      actor: 'You (Operator)',
      action: 'Updated status to RESOLVED',
      target: 'INC-204 (Production Database High Latency)',
      category: 'status',
      time: '10 minutes ago',
      details: 'Root cause identified: unindexed join query resolved with migration 008.',
    },
    {
      id: 'act-2',
      actor: 'AI Copilot Assistant',
      action: 'Synthesized draft Knowledge Article',
      target: 'KB-802 (Troubleshooting Postgres High Load)',
      category: 'ai',
      time: '25 minutes ago',
      details: 'Automatically generated from resolved ticket resolution notes.',
    },
    {
      id: 'act-3',
      actor: 'Alex Rivera',
      action: 'Assigned request to Network Team',
      target: 'REQ-109 (Provision VPN Access)',
      category: 'assignment',
      time: '2 hours ago',
      details: 'Reassigned from Support Triage to Security Engineering.',
    },
    {
      id: 'act-4',
      actor: 'Sarah Connor',
      action: 'Approved Change Request',
      target: 'CHG-301 (Deploy API v2.4 Release)',
      category: 'approval',
      time: 'Yesterday',
      details: 'CAB approval granted following successful staging deployment test.',
    },
    {
      id: 'act-5',
      actor: 'System Outbox Worker',
      action: 'Dispatched SLA Breach Alert',
      target: 'INC-198 (VPN Connection Timeout)',
      category: 'status',
      time: '2 days ago',
      details: 'Escalated to On-Call Manager due to 80% SLA window elapsed.',
    },
  ]

  const filteredActivities = activities.filter((act) => {
    if (filterType !== 'all' && act.category !== filterType) return false
    return true
  })

  function getCategoryIcon(cat: string) {
    switch (cat) {
      case 'comment': return <MessageSquare size={16} style={{ color: '#2563eb' }} />
      case 'status': return <CheckCircle size={16} style={{ color: '#16a34a' }} />
      case 'assignment': return <UserPlus size={16} style={{ color: '#7c3aed' }} />
      case 'approval': return <CheckCircle size={16} style={{ color: '#d97706' }} />
      case 'ai': return <Sparkles size={16} style={{ color: '#16a34a' }} />
      default: return <Activity size={16} style={{ color: '#64748b' }} />
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Personal & Team Activity Timeline</h1>
        <p className="page-subtitle">Chronological feed of comments, status transitions, assignments, CAB approvals, and AI agent actions</p>
      </div>

      {/* Filter Controls */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.85rem', fontWeight: 600, color: '#475569' }}>
          <Filter size={16} /> Filters:
        </div>
        <select value={filterRange} onChange={(e) => setFilterRange(e.target.value)} style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid #cbd5e1' }}>
          <option value="all">Timeframe: All History</option>
          <option value="today">Today</option>
          <option value="yesterday">Yesterday</option>
          <option value="week">Last 7 Days</option>
        </select>
        <select value={filterType} onChange={(e) => setFilterType(e.target.value)} style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid #cbd5e1' }}>
          <option value="all">Category: All Types</option>
          <option value="status">Status Changes</option>
          <option value="assignment">Assignments</option>
          <option value="approval">Approvals</option>
          <option value="ai">AI Actions</option>
        </select>
      </div>

      {/* Timeline Stream */}
      <div className="panel">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {filteredActivities.map((item) => (
            <div
              key={item.id}
              style={{
                display: 'flex',
                gap: 14,
                paddingBottom: 16,
                borderBottom: '1px solid #f1f5f9',
              }}
            >
              <div
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: '50%',
                  background: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                {getCategoryIcon(item.category)}
              </div>

              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>
                    {item.actor} <span style={{ fontWeight: 'normal', color: '#64748b' }}>{item.action}</span>
                  </span>
                  <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Clock size={12} /> {item.time}
                  </span>
                </div>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#16a34a', marginBottom: 4 }}>
                  {item.target}
                </div>
                <div style={{ fontSize: '0.8rem', color: '#475569', background: '#f8fafc', padding: '6px 10px', borderRadius: 6, border: '1px solid #f1f5f9' }}>
                  {item.details}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
