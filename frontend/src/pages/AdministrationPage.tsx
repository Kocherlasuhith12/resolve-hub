import { useActiveOrganisation } from '../hooks/useActiveOrganisation'
import { AdministrationWorkspace } from '../features/administration/AdministrationWorkspace'

export function AdministrationPage() {
  const { organisationId, isLoading } = useActiveOrganisation()

  if (isLoading || !organisationId) {
    return <div className="section-message" role="status"><div className="loading-spinner" /> Loading administration workspace…</div>
  }

  return <AdministrationWorkspace organisationId={organisationId} />
}
