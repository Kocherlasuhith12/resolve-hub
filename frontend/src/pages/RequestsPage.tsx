import { useActiveOrganisation } from '../hooks/useActiveOrganisation'
import { TicketWorkspace } from '../features/tickets/TicketWorkspace'

export function RequestsPage() {
  const { organisationId, isLoading, isError } = useActiveOrganisation()

  if (isLoading && !organisationId) {
    return (
      <div className="section-message" role="status">
        <div className="loading-spinner" /> Loading requests workspace…
      </div>
    )
  }

  if (isError || (!isLoading && !organisationId)) {
    return (
      <div className="form-error organisation-state" role="alert">
        No active organisation found. Please select or set up a workspace to continue.
      </div>
    )
  }

  return <TicketWorkspace organisationId={organisationId} />
}
