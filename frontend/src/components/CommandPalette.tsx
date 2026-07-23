import { useEffect, useState } from 'react'
import {
  Search,
  LayoutDashboard,
  Ticket,
  BookOpen,
  Bell,
  Settings,
  Plus,
  Sparkles,
  Command,
  HardDrive,
  BarChart3,
  Building,
  Palette,
  CreditCard,
  HelpCircle,
  Activity,
  ShieldCheck,
  User,
} from 'lucide-react'

type CommandPaletteProps = {
  isOpen: boolean
  onClose: () => void
  onNavigate: (routePath: string) => void
}

export function CommandPalette({ isOpen, onClose, onNavigate }: CommandPaletteProps) {
  const [query, setQuery] = useState('')

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        if (isOpen) {
          onClose()
        }
      }
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  if (!isOpen) return null

  const actions = [
    { id: 'nav-dashboard', label: 'Go to Operations Dashboard', icon: LayoutDashboard, category: 'Operations', path: '/dashboard' },
    { id: 'nav-tickets', label: 'Go to Ticket Requests', icon: Ticket, category: 'Operations', path: '/requests' },
    { id: 'nav-incidents', label: 'Filter Incidents', icon: Ticket, category: 'Operations', path: '/incidents' },
    { id: 'nav-problems', label: 'View Problems & Root Causes', icon: Ticket, category: 'Operations', path: '/problems' },
    { id: 'nav-changes', label: 'View Change Requests', icon: Ticket, category: 'Operations', path: '/changes' },
    { id: 'nav-assets', label: 'Go to Asset Inventory', icon: HardDrive, category: 'Operations', path: '/assets' },
    { id: 'nav-kb', label: 'Go to Knowledge Base', icon: BookOpen, category: 'Knowledge & AI', path: '/knowledge' },
    { id: 'nav-copilot', label: 'Open AI Copilot Assistant', icon: Sparkles, category: 'Knowledge & AI', path: '/copilot' },
    { id: 'nav-analytics', label: 'Go to Analytics & Metrics', icon: BarChart3, category: 'Knowledge & AI', path: '/analytics' },
    { id: 'nav-workspace', label: 'Workspace Settings & Profile', icon: Building, category: 'Workspace', path: '/settings/workspace' },
    { id: 'nav-appearance', label: 'Appearance & Custom Theme', icon: Palette, category: 'Workspace', path: '/settings/appearance' },
    { id: 'nav-system', label: 'System Settings & Diagnostics', icon: Settings, category: 'Workspace', path: '/settings/system' },
    { id: 'nav-billing', label: 'Billing & Plan Usage', icon: CreditCard, category: 'Workspace', path: '/settings/billing' },
    { id: 'nav-help', label: 'Help & Support Hub', icon: HelpCircle, category: 'Workspace', path: '/help' },
    { id: 'nav-profile', label: 'My User Profile', icon: User, category: 'Personal', path: '/profile' },
    { id: 'nav-activity', label: 'Personal & Team Activity Feed', icon: Activity, category: 'Personal', path: '/activity' },
    { id: 'nav-notifications', label: 'Notifications & Alerts', icon: Bell, category: 'Personal', path: '/notifications' },
    { id: 'nav-audit', label: 'Administrator Audit Logs', icon: ShieldCheck, category: 'Administration', path: '/audit-logs' },
    { id: 'action-create', label: 'Create New Service Request', icon: Plus, category: 'Actions', path: '/requests' },
  ]

  const filtered = actions.filter(
    (action) =>
      action.label.toLowerCase().includes(query.toLowerCase()) ||
      action.category.toLowerCase().includes(query.toLowerCase()),
  )

  return (
    <div className="command-palette-backdrop" onClick={onClose}>
      <div
        className="command-palette-modal"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-label="Command palette"
      >
        <div className="command-palette-search">
          <Search size={18} className="search-icon" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or search… (Cmd + K)"
            autoFocus
          />
          <kbd className="cmd-kbd"><Command size={10} /> K</kbd>
        </div>

        <div className="command-palette-results">
          {filtered.length === 0 ? (
            <div className="empty-results">No matching commands found.</div>
          ) : (
            filtered.map((item) => {
              const Icon = item.icon
              return (
                <div
                  key={item.id}
                  className="command-palette-item"
                  onClick={() => {
                    onNavigate(item.path)
                    onClose()
                  }}
                >
                  <Icon size={16} />
                  <span className="item-label">{item.label}</span>
                  <span className="item-category">{item.category}</span>
                </div>
              )
            })
          )}
        </div>
      </div>
    </div>
  )
}
