import { useActiveOrganisation } from '../hooks/useActiveOrganisation'
import { IncidentsWorkspace } from '../features/incidents/IncidentsWorkspace'

export function IncidentsPage() {
  const { organisationId, isLoading, isError } = useActiveOrganisation()

  if (isLoading && !organisationId) {
    return (
      <div className="section-message" role="status">
        <div className="loading-spinner" /> Loading incident command workspace…
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

  return <IncidentsWorkspace organisationId={organisationId} />
}
