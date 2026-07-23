import { useActiveOrganisation } from '../hooks/useActiveOrganisation'
import { NotificationCenter } from '../features/notifications/NotificationCenter'

export function NotificationsPage() {
  const { organisationId, isLoading } = useActiveOrganisation()

  if (isLoading || !organisationId) {
    return <div className="section-message" role="status"><div className="loading-spinner" /> Loading notifications workspace…</div>
  }

  return <NotificationCenter organisationId={organisationId} />
}
