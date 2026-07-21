import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ApiError } from '../../api/client'
import { useAuth } from '../../auth/useAuth'

type SuggestionStatus = 'PENDING' | 'ACCEPTED' | 'REJECTED'
type SuggestionKind = 'CATEGORY' | 'PRIORITY' | 'DUPLICATE' | 'SUMMARY' | 'RESPONSE'

type AiSuggestion = {
  id: string
  run_id: string
  ticket_id: string
  kind: SuggestionKind
  value: Record<string, unknown>
  confidence: number
  meets_threshold: boolean
  status: SuggestionStatus
  decided_by_id: string | null
  decided_at: string | null
  created_at: string
}

type AiSuggestionList = { items: AiSuggestion[] }
type AiRun = {
  id: string
  status: string
  provider: string
  model_name: string
  prompt_version: string
  latency_ms: number | null
  suggestions: AiSuggestion[]
}

const labels: Record<SuggestionKind, string> = {
  CATEGORY: 'Category recommendation',
  PRIORITY: 'Priority recommendation',
  DUPLICATE: 'Possible duplicates',
  SUMMARY: 'Suggested summary',
  RESPONSE: 'Suggested response',
}

function textValue(value: unknown): string {
  return typeof value === 'string' ? value : 'Not provided'
}

function SuggestionValue({ suggestion }: { suggestion: AiSuggestion }) {
  if (suggestion.kind === 'CATEGORY') {
    return (
      <p>
        Category ID: <code>{textValue(suggestion.value.category_id)}</code>
        {typeof suggestion.value.reason === 'string' ? ` — ${suggestion.value.reason}` : ''}
      </p>
    )
  }
  if (suggestion.kind === 'PRIORITY') {
    return <p>Suggested priority: <strong>{textValue(suggestion.value.priority)}</strong></p>
  }
  if (suggestion.kind === 'DUPLICATE') {
    const ids = Array.isArray(suggestion.value.ticket_ids)
      ? suggestion.value.ticket_ids.filter((item): item is string => typeof item === 'string')
      : []
    return ids.length > 0 ? (
      <p>Potential ticket IDs: {ids.join(', ')}</p>
    ) : (
      <p>No likely duplicate was identified.</p>
    )
  }
  if (suggestion.kind === 'SUMMARY') {
    return <p>{textValue(suggestion.value.summary)}</p>
  }
  return <p>{textValue(suggestion.value.response)}</p>
}

export function AiReviewPanel({
  organisationId,
  ticketId,
  permissions,
}: {
  organisationId: string
  ticketId: string
  permissions: string[]
}) {
  const { request } = useAuth()
  const queryClient = useQueryClient()
  const canSuggest = permissions.includes('ai:suggest')
  const canReview = permissions.includes('ai:review')
  const queryKey = ['ai-suggestions', organisationId, ticketId]
  const suggestions = useQuery({
    queryKey,
    queryFn: () =>
      request<AiSuggestionList>(
        `/organisations/${organisationId}/tickets/${ticketId}/ai/suggestions`,
      ),
    enabled: canSuggest,
  })
  const generate = useMutation({
    mutationFn: () =>
      request<AiRun>(`/organisations/${organisationId}/tickets/${ticketId}/ai/suggestions`, {
        method: 'POST',
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey })
    },
  })
  const decide = useMutation({
    mutationFn: ({ suggestionId, status }: { suggestionId: string; status: 'ACCEPTED' | 'REJECTED' }) =>
      request<AiSuggestion>(
        `/organisations/${organisationId}/tickets/${ticketId}/ai/suggestions/${suggestionId}/decision`,
        { method: 'POST', body: JSON.stringify({ status }) },
      ),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey })
    },
  })

  if (!canSuggest) return null

  const items = suggestions.data?.items ?? []
  const generationError = generate.error
  const unavailable = generationError instanceof ApiError
    && ['AI_DISABLED', 'AI_UNAVAILABLE'].includes(generationError.code)

  return (
    <section className="ai-review" aria-labelledby="ai-review-title">
      <div className="ai-review-heading">
        <div>
          <p className="card-label">Optional assistance</p>
          <h3 id="ai-review-title">AI suggestions with human review</h3>
          <p>Suggestions are advisory. Accepting one records your decision but never changes this ticket.</p>
        </div>
        <button
          className="quiet-button"
          type="button"
          disabled={generate.isPending}
          onClick={() => generate.mutate()}
        >
          {generate.isPending ? 'Generating…' : 'Generate suggestions'}
        </button>
      </div>

      {suggestions.isPending && <p className="section-message" role="status">Loading AI suggestions…</p>}
      {suggestions.isError && (
        <div className="form-error" role="alert">Existing AI suggestions could not be loaded.</div>
      )}
      {unavailable && (
        <div className="ai-unavailable" role="status">
          AI assistance is currently unavailable. Ticket operations continue normally.
        </div>
      )}
      {generate.isError && !unavailable && (
        <div className="form-error" role="alert">Suggestions could not be generated.</div>
      )}
      {decide.isError && (
        <div className="form-error" role="alert">That decision could not be recorded. Refresh and try again.</div>
      )}
      {!suggestions.isPending && !suggestions.isError && items.length === 0 && (
        <p className="muted">No suggestions have been requested for this ticket.</p>
      )}
      {items.length > 0 && (
        <div className="ai-suggestion-list" aria-live="polite">
          {items.map((suggestion) => (
            <article key={suggestion.id} className="ai-suggestion">
              <div className="ai-suggestion-header">
                <div>
                  <h4>{labels[suggestion.kind]}</h4>
                  <span>{Math.round(suggestion.confidence * 100)}% confidence</span>
                </div>
                <strong className={`ai-status ai-status-${suggestion.status.toLowerCase()}`}>
                  {suggestion.status.toLowerCase()}
                </strong>
              </div>
              <SuggestionValue suggestion={suggestion} />
              {!suggestion.meets_threshold && (
                <p className="ai-threshold-warning">Below the configured confidence threshold.</p>
              )}
              {suggestion.status === 'PENDING' && canReview && (
                <div className="ai-decision-actions">
                  <button
                    className="quiet-button"
                    type="button"
                    disabled={decide.isPending}
                    onClick={() => decide.mutate({ suggestionId: suggestion.id, status: 'ACCEPTED' })}
                  >
                    Accept suggestion
                  </button>
                  <button
                    className="text-button"
                    type="button"
                    disabled={decide.isPending}
                    onClick={() => decide.mutate({ suggestionId: suggestion.id, status: 'REJECTED' })}
                  >
                    Reject suggestion
                  </button>
                </div>
              )}
              {suggestion.status !== 'PENDING' && (
                <small>Decision recorded only; the ticket was not changed.</small>
              )}
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
