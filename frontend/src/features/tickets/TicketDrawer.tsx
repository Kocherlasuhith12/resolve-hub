import { X } from 'lucide-react'
import { TicketDetail } from './TicketDetail'

export function TicketDrawer({
  isOpen,
  organisationId,
  ticketId,
  permissions,
  onClose,
}: {
  isOpen: boolean
  organisationId: string
  ticketId: string | null
  permissions: string[]
  onClose: () => void
}) {
  if (!isOpen || !ticketId) return null

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <span className="card-label">Ticket Inspector</span>
          <button className="btn-icon" type="button" onClick={onClose} aria-label="Close drawer">
            <X size={18} />
          </button>
        </div>
        <div className="drawer-body">
          <TicketDetail
            organisationId={organisationId}
            ticketId={ticketId}
            permissions={permissions}
            onBack={onClose}
          />
        </div>
      </div>
    </div>
  )
}
