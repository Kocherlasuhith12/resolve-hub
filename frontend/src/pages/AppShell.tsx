import { useState, type ReactNode } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  LayoutDashboard,
  Ticket,
  AlertTriangle,
  FileCode,
  Layers,
  HardDrive,
  BookOpen,
  BarChart3,
  Sparkles,
  Bell,
  Settings,
  Search,
  Plus,
  ChevronLeft,
  ChevronRight,
  Command,
  Building2,
  Palette,
  CreditCard,
  HelpCircle,
  Activity,
  ShieldCheck,
  User,
  Sliders,
} from 'lucide-react'
import { Brand } from '../components/Brand'
import { ProfileDropdown } from '../components/ProfileDropdown'
import { CommandPalette } from '../components/CommandPalette'
import { useAuth } from '../auth/useAuth'

type Organisation = {
  id: string
  name: string
  slug: string
  is_active: boolean
}

type MembershipContext = {
  permissions: string[]
}

export function AppShell({ children }: { children?: ReactNode }) {
  const { user, request } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [selectedId, setSelectedId] = useState<string>(() => {
    return (typeof window !== 'undefined' && localStorage.getItem('resolvehub_active_org_id')) || ''
  })
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false)
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false)

  const firstName = user?.display_name.split(/\s|@/)[0] || 'there'

  const organisations = useQuery({
    queryKey: ['organisations'],
    queryFn: () => request<Organisation[]>('/organisations'),
  })

  const items = organisations.data ?? []
  const activeId = selectedId || items[0]?.id || ''
  const activeOrganisation = items.find((item) => item.id === activeId)

  const membership = useQuery({
    queryKey: ['membership', activeId],
    queryFn: () => request<MembershipContext>(`/organisations/${activeId}/membership/me`),
    enabled: Boolean(activeId),
  })

  const permissions = membership.data?.permissions ?? []
  const canReadNotifications = permissions.includes('notification:read')
  const canAdminister = [
    'member:invite',
    'member:read',
    'department:create',
    'category:create',
    'sla:manage',
  ].some((permission) => permissions.includes(permission))

  const initials = (user?.display_name || user?.email || '?')
    .split(/\s|@/)
    .slice(0, 2)
    .map((s) => s[0]?.toUpperCase() || '')
    .join('')

  const currentPath = location.pathname

  function handleNavigate(path: string) {
    navigate(path)
  }

  return (
    <div className="app-frame">
      {/* ---- Top Navigation ---- */}
      <header className="app-topnav">
        <div className="topnav-left">
          <button
            className="sidebar-toggle-btn"
            type="button"
            onClick={() => setSidebarCollapsed((prev) => !prev)}
            aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {sidebarCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          </button>
          <Brand />
        </div>

        <div
          className="topnav-search"
          onClick={() => setCommandPaletteOpen(true)}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && setCommandPaletteOpen(true)}
        >
          <Search size={16} className="topnav-search-icon" />
          <input
            type="search"
            readOnly
            onFocus={() => setCommandPaletteOpen(true)}
            placeholder="Search tickets, articles, commands… (Cmd + K)"
          />
          <kbd className="cmd-hint"><Command size={10} /> K</kbd>
        </div>

        <div className="topnav-actions">
          {canReadNotifications && (
            <button
              className="topnav-icon-btn"
              type="button"
              aria-label="Notifications"
              onClick={() => handleNavigate('/notifications')}
            >
              <Bell size={18} />
            </button>
          )}
          <button
            className="topnav-icon-btn"
            type="button"
            aria-label="Create new ticket"
            onClick={() => handleNavigate('/requests')}
          >
            <Plus size={18} />
          </button>
          <span className="topnav-divider" />

          <div style={{ position: 'relative' }}>
            <button
              className="topnav-profile"
              type="button"
              aria-expanded={profileDropdownOpen}
              onClick={() => setProfileDropdownOpen((prev) => !prev)}
            >
              <span className="profile-avatar">{initials}</span>
              <span>{firstName}</span>
            </button>

            <ProfileDropdown
              isOpen={profileDropdownOpen}
              onClose={() => setProfileDropdownOpen(false)}
              onNavigate={(routePath) => handleNavigate(routePath)}
            />
          </div>
        </div>
      </header>

      {/* ---- Command Palette Modal ---- */}
      <CommandPalette
        isOpen={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
        onNavigate={(routePath) => handleNavigate(routePath)}
      />

      {/* ---- Body: Sidebar + Main ---- */}
      <div className="app-body">
        {/* Sidebar Navigation */}
        <nav className={`app-sidebar ${sidebarCollapsed ? 'collapsed' : ''}`} aria-label="Workspace sections">
          {/* Organisation Selector */}
          {activeOrganisation && (
            <div className="org-selector">
              <span className="org-selector-icon">{activeOrganisation.name[0]?.toUpperCase()}</span>
              <div className="org-selector-info">
                <div className="org-selector-name">{activeOrganisation.name}</div>
                <div className="org-selector-slug">{activeOrganisation.slug}</div>
              </div>
            </div>
          )}

          {items.length > 1 && (
            <label className="organisation-select" style={{ padding: '0 12px', marginBottom: 8 }}>
              <span className="sr-only">Organisation</span>
              <select
                value={activeId}
                onChange={(event) => {
                  const val = event.target.value
                  setSelectedId(val)
                  localStorage.setItem('resolvehub_active_org_id', val)
                }}
              >
                {items.map((organisation) => (
                  <option key={organisation.id} value={organisation.id}>{organisation.name}</option>
                ))}
              </select>
            </label>
          )}

          {/* Operations Section */}
          <span className="sidebar-section-title">Operations</span>

          <button
            className="sidebar-nav-item"
            type="button"
            aria-current={currentPath === '/dashboard' || currentPath === '/' ? 'page' : undefined}
            onClick={() => handleNavigate('/dashboard')}
          >
            <LayoutDashboard size={18} />
            <span className="sidebar-label">Dashboard</span>
          </button>

          <button
            className="sidebar-nav-item"
            type="button"
            aria-current={currentPath === '/requests' ? 'page' : undefined}
            onClick={() => handleNavigate('/requests')}
          >
            <Ticket size={18} />
            <span className="sidebar-label">Requests</span>
          </button>

          <button
            className="sidebar-nav-item"
            type="button"
            aria-current={currentPath === '/incidents' ? 'page' : undefined}
            onClick={() => handleNavigate('/incidents')}
          >
            <AlertTriangle size={18} />
            <span className="sidebar-label">Incidents</span>
          </button>

          <button
            className="sidebar-nav-item"
            type="button"
            aria-current={currentPath === '/problems' ? 'page' : undefined}
            onClick={() => handleNavigate('/problems')}
          >
            <FileCode size={18} />
            <span className="sidebar-label">Problems</span>
          </button>

          <button
            className="sidebar-nav-item"
            type="button"
            aria-current={currentPath === '/changes' ? 'page' : undefined}
            onClick={() => handleNavigate('/changes')}
          >
            <Layers size={18} />
            <span className="sidebar-label">Changes</span>
          </button>

          <button
            className="sidebar-nav-item"
            type="button"
            aria-current={currentPath === '/assets' ? 'page' : undefined}
            onClick={() => handleNavigate('/assets')}
          >
            <HardDrive size={18} />
            <span className="sidebar-label">Assets</span>
          </button>

          {/* Knowledge & AI Section */}
          <span className="sidebar-section-title">Knowledge & AI</span>

          <button
            className="sidebar-nav-item"
            type="button"
            aria-current={currentPath === '/knowledge' ? 'page' : undefined}
            onClick={() => handleNavigate('/knowledge')}
          >
            <BookOpen size={18} />
            <span className="sidebar-label">Knowledge Base</span>
          </button>

          <button
            className="sidebar-nav-item"
            type="button"
            aria-current={currentPath === '/copilot' ? 'page' : undefined}
            onClick={() => handleNavigate('/copilot')}
          >
            <Sparkles size={18} />
            <span className="sidebar-label">AI Copilot</span>
          </button>

          <button
            className="sidebar-nav-item"
            type="button"
            aria-current={currentPath === '/analytics' ? 'page' : undefined}
            onClick={() => handleNavigate('/analytics')}
          >
            <BarChart3 size={18} />
            <span className="sidebar-label">Analytics</span>
          </button>

          {/* Administration Section */}
          {canAdminister && (
            <>
              <span className="sidebar-section-title">Administration</span>
              <button
                className="sidebar-nav-item"
                type="button"
                aria-current={currentPath === '/administration' ? 'page' : undefined}
                onClick={() => handleNavigate('/administration')}
              >
                <Sliders size={18} />
                <span className="sidebar-label">Administration</span>
              </button>

              <button
                className="sidebar-nav-item"
                type="button"
                aria-current={currentPath === '/audit-logs' ? 'page' : undefined}
                onClick={() => handleNavigate('/audit-logs')}
              >
                <ShieldCheck size={18} />
                <span className="sidebar-label">Audit Logs</span>
              </button>
            </>
          )}

          {/* Workspace Section */}
          <span className="sidebar-section-title">Workspace</span>

          <button
            className="sidebar-nav-item"
            type="button"
            aria-current={currentPath === '/settings/workspace' || currentPath === '/settings' ? 'page' : undefined}
            onClick={() => handleNavigate('/settings/workspace')}
          >
            <Building2 size={18} />
            <span className="sidebar-label">Workspace Settings</span>
          </button>

          <button
            className="sidebar-nav-item"
            type="button"
            aria-current={currentPath === '/settings/appearance' ? 'page' : undefined}
            onClick={() => handleNavigate('/settings/appearance')}
          >
            <Palette size={18} />
            <span className="sidebar-label">Appearance & Theme</span>
          </button>

          <button
            className="sidebar-nav-item"
            type="button"
            aria-current={currentPath === '/settings/system' ? 'page' : undefined}
            onClick={() => handleNavigate('/settings/system')}
          >
            <Settings size={18} />
            <span className="sidebar-label">System Settings</span>
          </button>

          <button
            className="sidebar-nav-item"
            type="button"
            aria-current={currentPath === '/settings/billing' ? 'page' : undefined}
            onClick={() => handleNavigate('/settings/billing')}
          >
            <CreditCard size={18} />
            <span className="sidebar-label">Billing & Plan</span>
          </button>

          <button
            className="sidebar-nav-item"
            type="button"
            aria-current={currentPath === '/help' ? 'page' : undefined}
            onClick={() => handleNavigate('/help')}
          >
            <HelpCircle size={18} />
            <span className="sidebar-label">Help & Support</span>
          </button>

          {/* Personal Section */}
          <span className="sidebar-section-title">Personal</span>

          <button
            className="sidebar-nav-item"
            type="button"
            aria-current={currentPath === '/profile' ? 'page' : undefined}
            onClick={() => handleNavigate('/profile')}
          >
            <User size={18} />
            <span className="sidebar-label">My Profile</span>
          </button>

          {canReadNotifications && (
            <button
              className="sidebar-nav-item"
              type="button"
              aria-current={currentPath === '/notifications' ? 'page' : undefined}
              onClick={() => handleNavigate('/notifications')}
            >
              <Bell size={18} />
              <span className="sidebar-label">Notifications</span>
            </button>
          )}

          <button
            className="sidebar-nav-item"
            type="button"
            aria-current={currentPath === '/activity' ? 'page' : undefined}
            onClick={() => handleNavigate('/activity')}
          >
            <Activity size={18} />
            <span className="sidebar-label">Activity Timeline</span>
          </button>

          <div className="sidebar-spacer" />
        </nav>

        {/* Main Content Area */}
        <main className="app-main">
          {organisations.isPending && <p className="section-message" role="status">Loading workspace…</p>}
          {organisations.isError && (
            <div className="form-error organisation-state" role="alert">
              Organisations could not be loaded. Sign out and try again.
            </div>
          )}

          {!organisations.isPending && !organisations.isError && children}
        </main>
      </div>
    </div>
  )
}
