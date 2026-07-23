import { useRef, useEffect } from 'react'
import {
  User,
  Building,
  Bell,
  Palette,
  Settings,
  CreditCard,
  HelpCircle,
  LogOut,
  Activity,
} from 'lucide-react'
import { useAuth } from '../auth/useAuth'

export function ProfileDropdown({
  isOpen,
  onClose,
  onNavigate,
}: {
  isOpen: boolean
  onClose: () => void
  onNavigate: (routePath: string) => void
}) {
  const { user, logout } = useAuth()
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        onClose()
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div className="profile-dropdown" ref={ref} role="menu" aria-label="User menu">
      <div className="profile-dropdown-header">
        <strong>{user?.display_name || 'User'}</strong>
        <small>{user?.email}</small>
      </div>

      <div className="profile-dropdown-menu">
        <button
          type="button"
          role="menuitem"
          onClick={() => {
            onNavigate('/profile')
            onClose()
          }}
        >
          <User size={16} /> My Profile
        </button>
        <button
          type="button"
          role="menuitem"
          onClick={() => {
            onNavigate('/settings/workspace')
            onClose()
          }}
        >
          <Building size={16} /> Workspace Settings
        </button>
        <button
          type="button"
          role="menuitem"
          onClick={() => {
            onNavigate('/notifications')
            onClose()
          }}
        >
          <Bell size={16} /> Notifications
        </button>
        <button
          type="button"
          role="menuitem"
          onClick={() => {
            onNavigate('/settings/appearance')
            onClose()
          }}
        >
          <Palette size={16} /> Appearance & Theme
        </button>
        <button
          type="button"
          role="menuitem"
          onClick={() => {
            onNavigate('/settings/system')
            onClose()
          }}
        >
          <Settings size={16} /> System Settings
        </button>
        <button
          type="button"
          role="menuitem"
          onClick={() => {
            onNavigate('/settings/billing')
            onClose()
          }}
        >
          <CreditCard size={16} /> Billing & Plan
        </button>
        <button
          type="button"
          role="menuitem"
          onClick={() => {
            onNavigate('/activity')
            onClose()
          }}
        >
          <Activity size={16} /> Activity Feed
        </button>
        <button
          type="button"
          role="menuitem"
          onClick={() => {
            onNavigate('/help')
            onClose()
          }}
        >
          <HelpCircle size={16} /> Help & Support
        </button>

        <span className="profile-dropdown-divider" />

        <button
          type="button"
          role="menuitem"
          className="danger-item"
          onClick={() => void logout()}
        >
          <LogOut size={16} /> Sign Out
        </button>
      </div>
    </div>
  )
}
