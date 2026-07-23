import { useActiveOrganisation } from '../hooks/useActiveOrganisation'
import { AiCopilotWorkspace } from '../features/ai/AiCopilotWorkspace'

export function AiCopilotPage() {
  const { organisationId, isLoading, isError } = useActiveOrganisation()

  if (isLoading && !organisationId) {
    return (
      <div className="section-message" role="status">
        <div className="loading-spinner" /> Loading AI Copilot workspace…
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

  return <AiCopilotWorkspace organisationId={organisationId} />
}
