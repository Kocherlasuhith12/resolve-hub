import { useState } from 'react'
import { Search, HelpCircle, Command, MessageSquare, BookOpen, ExternalLink, Check, ChevronDown, ChevronUp } from 'lucide-react'

export function HelpSupportPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [activeFaq, setActiveFaq] = useState<number | null>(0)
  const [showShortcuts, setShowShortcuts] = useState(false)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  const faqs = [
    {
      q: 'How do SLA breach calculations work in ResolveHub?',
      a: 'SLA windows calculate target response and resolution times based on defined business hours and ticket priority. When an SLA warning threshold (80%) is reached, outbox events trigger WebSocket notifications and Temporal workflow escalations.',
    },
    {
      q: 'Can I restrict member permissions by department?',
      a: 'Yes! ResolveHub uses fine-grained permission strings (e.g. ticket:read, ticket:write, member:invite). Roles can be assigned per tenant member and scoped to specific departmental categories.',
    },
    {
      q: 'How does the AI Copilot generate knowledge articles?',
      a: 'When an operator resolves a complex incident, the AI Copilot analyzes the resolution notes and root cause to synthesize draft knowledge base articles automatically.',
    },
    {
      q: 'Where can I find full API documentation?',
      a: 'Interactive OpenAPI Swagger documentation is available at /docs, and raw OpenAPI JSON schemas can be inspected at /openapi.json on your server.',
    },
  ]

  const shortcuts = [
    { key: 'Cmd + K', action: 'Open Global Command Palette' },
    { key: 'Shift + N', action: 'Quick Create New Request' },
    { key: 'g + d', action: 'Navigate to Operations Dashboard' },
    { key: 'g + r', action: 'Navigate to Requests List' },
    { key: 'g + i', action: 'Navigate to Incidents' },
    { key: 'g + k', action: 'Navigate to Knowledge Base' },
    { key: 'Esc', action: 'Close Modal or Slide-over Inspector' },
  ]

  function handleSubmitForm(type: string) {
    setSuccessMsg(`${type} submitted successfully! Support ticket created for your account.`)
    setTimeout(() => setSuccessMsg(null), 4000)
  }

  return (
    <div>
      <div className="page-header">
        <h1>Help & Support Hub</h1>
        <p className="page-subtitle">Access documentation, keyboard shortcuts, system status, and reach out to engineering support</p>
      </div>

      {successMsg && (
        <div className="form-success" role="status" style={{ marginBottom: 20 }}>
          <Check size={16} style={{ display: 'inline', marginRight: 6 }} />
          {successMsg}
        </div>
      )}

      {/* Docs Search Hero */}
      <div
        style={{
          background: 'linear-gradient(135deg, #16A34A 0%, #15803D 100%)',
          color: '#ffffff',
          padding: '32px 24px',
          borderRadius: 12,
          marginBottom: 24,
          boxShadow: '0 4px 12px rgba(22, 163, 74, 0.15)',
        }}
      >
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 8 }}>How can we help you today?</h2>
        <p style={{ opacity: 0.9, marginBottom: 16, fontSize: '0.95rem' }}>
          Search operator guides, API references, or launch quick support tickets
        </p>

        <div style={{ position: 'relative', maxWidth: 600 }}>
          <Search size={18} style={{ position: 'absolute', left: 14, top: 14, color: '#64748b' }} />
          <input
            type="search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search guides, SLAs, API documentation..."
            style={{
              width: '100%',
              padding: '12px 16px 12px 42px',
              borderRadius: 8,
              border: 'none',
              fontSize: '0.95rem',
              outline: 'none',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            }}
          />
        </div>
      </div>

      {/* Quick Action Badges */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
        <button
          className="btn-secondary"
          type="button"
          onClick={() => setShowShortcuts(true)}
          style={{ display: 'flex', alignItems: 'center', gap: 6 }}
        >
          <Command size={16} /> Keyboard Shortcuts (Cmd + K)
        </button>
        <a
          href="/docs"
          target="_blank"
          rel="noreferrer"
          className="btn-secondary"
          style={{ display: 'inline-flex', alignItems: 'center', gap: 6, textDecoration: 'none' }}
        >
          <BookOpen size={16} /> API Reference <ExternalLink size={12} />
        </a>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: '0.85rem', padding: '6px 12px', background: '#dcfce7', color: '#15803d', borderRadius: 6, fontWeight: 600 }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#16a34a', display: 'inline-block' }} /> All Systems Operational (v0.1.0)
        </div>
      </div>

      <div className="dashboard-panels">
        {/* FAQs */}
        <div className="panel">
          <div className="panel-header">
            <h3><HelpCircle size={18} style={{ display: 'inline', marginRight: 6 }} /> Frequently Asked Questions</h3>
          </div>
          <div style={{ marginTop: 12 }}>
            {faqs.map((faq, idx) => {
              const isOpen = activeFaq === idx
              return (
                <div
                  key={faq.q}
                  style={{
                    border: '1px solid #e2e8f0',
                    borderRadius: 8,
                    marginBottom: 10,
                    overflow: 'hidden',
                  }}
                >
                  <button
                    type="button"
                    onClick={() => setActiveFaq(isOpen ? null : idx)}
                    style={{
                      width: '100%',
                      padding: 14,
                      textAlign: 'left',
                      background: isOpen ? '#f8fafc' : '#ffffff',
                      border: 'none',
                      fontWeight: 600,
                      fontSize: '0.9rem',
                      cursor: 'pointer',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <span>{faq.q}</span>
                    {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </button>
                  {isOpen && (
                    <div style={{ padding: '0 14px 14px 14px', fontSize: '0.85rem', color: '#475569', lineHeight: 1.5, background: '#f8fafc' }}>
                      {faq.a}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* Support & Feedback Forms */}
        <div className="panel">
          <div className="panel-header">
            <h3><MessageSquare size={18} style={{ display: 'inline', marginRight: 6 }} /> Contact Engineering Support</h3>
          </div>
          <form className="compact-form" onSubmit={(e) => { e.preventDefault(); handleSubmitForm('Support request') }}>
            <label>
              <span>Topic</span>
              <select defaultValue="Technical Support">
                <option value="Technical Support">Technical Support</option>
                <option value="Bug Report">Bug Report</option>
                <option value="Feature Request">Feature Request</option>
                <option value="Billing Query">Billing Query</option>
              </select>
            </label>
            <label>
              <span>Subject</span>
              <input required placeholder="Brief description of your issue" />
            </label>
            <label>
              <span>Details & Reproduction Steps</span>
              <textarea required rows={4} placeholder="Include relevant ticket IDs, URL, or error text..." />
            </label>
            <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
              <button className="btn-primary" type="submit">
                Submit Support Ticket
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Keyboard Shortcuts Modal */}
      {showShortcuts && (
        <div className="modal-backdrop" onClick={() => setShowShortcuts(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 480 }}>
            <div className="modal-header">
              <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Command size={18} /> Keyboard Shortcuts Cheat Sheet
              </h3>
            </div>
            <div className="modal-body" style={{ padding: '16px 0' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {shortcuts.map((s) => (
                  <div key={s.key} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: '#f8fafc', borderRadius: 6, border: '1px solid #e2e8f0' }}>
                    <span style={{ fontSize: '0.85rem', color: '#334155' }}>{s.action}</span>
                    <kbd style={{ background: '#ffffff', border: '1px solid #cbd5e1', borderRadius: 4, padding: '2px 8px', fontSize: '0.8rem', fontFamily: 'monospace', fontWeight: 600 }}>{s.key}</kbd>
                  </div>
                ))}
              </div>
            </div>
            <div className="modal-actions" style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button className="btn-secondary" type="button" onClick={() => setShowShortcuts(false)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
