import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import { readCookie } from '../../api/client'
import { useAuth } from '../../auth/useAuth'
import { AiReviewPanel } from './AiReviewPanel'

type AttachmentItem = {
  id: string
  original_filename: string
  content_type: string
  size_bytes: number
  upload_completed: boolean
  scan_status: 'PENDING' | 'CLEAN' | 'INFECTED' | 'FAILED'
  created_at: string
}

type TicketDetailRecord = {
  id: string
  ticket_number: string
  title: string
  description: string
  priority: string
  status: string
  sla_state: string
  assigned_agent_id: string | null
  version: number
  first_response_deadline: string | null
  resolution_deadline: string | null
  created_at: string
  updated_at: string
}

type Comment = {
  id: string
  author_id: string
  kind: 'PUBLIC' | 'INTERNAL'
  body: string
  created_at: string
}

type CommentPage = { items: Comment[]; next_cursor: string | null }

type TimelineEvent = {
  id: string
  event_type: string
  actor_type: string
  created_at: string
}

type TimelinePage = { items: TimelineEvent[]; next_cursor: string | null }

type AssignmentCandidate = {
  user_id: string
  display_name: string
}

const transitions: Record<string, string[]> = {
  DRAFT: ['SUBMITTED', 'CANCELLED'],
  SUBMITTED: ['TRIAGED', 'CANCELLED'],
  TRIAGED: ['ASSIGNED', 'IN_PROGRESS', 'CANCELLED'],
  ASSIGNED: ['IN_PROGRESS', 'CANCELLED'],
  IN_PROGRESS: ['WAITING_FOR_REQUESTER', 'RESOLVED', 'ESCALATED', 'CANCELLED'],
  WAITING_FOR_REQUESTER: ['IN_PROGRESS', 'CANCELLED'],
  ESCALATED: ['IN_PROGRESS', 'RESOLVED'],
  RESOLVED: ['CLOSED', 'REOPENED'],
  REOPENED: ['ASSIGNED', 'IN_PROGRESS'],
  CLOSED: [],
  CANCELLED: [],
}

const reasonRequired = new Set(['CANCELLED', 'ESCALATED', 'REOPENED'])

function transitionPermission(status: string): string {
  return {
    RESOLVED: 'ticket:resolve',
    REOPENED: 'ticket:reopen',
    ESCALATED: 'ticket:escalate',
  }[status] ?? 'ticket:transition'
}

function readable(value: string): string {
  return value.replaceAll('_', ' ').toLowerCase().replace(/^./, (letter) => letter.toUpperCase())
}

export function TicketDetail({
  organisationId,
  ticketId,
  permissions,
  onBack,
}: {
  organisationId: string
  ticketId: string
  permissions: string[]
  onBack: () => void
}) {
  const { request, user } = useAuth()
  const queryClient = useQueryClient()
  const [transitionStatus, setTransitionStatus] = useState('')
  const [commentBody, setCommentBody] = useState('')
  const [commentKind, setCommentKind] = useState<'PUBLIC' | 'INTERNAL'>('PUBLIC')
  const permissionSet = new Set(permissions)
  const detail = useQuery({
    queryKey: ['ticket', organisationId, ticketId],
    queryFn: () =>
      request<TicketDetailRecord>(`/organisations/${organisationId}/tickets/${ticketId}`),
  })
  const comments = useQuery({
    queryKey: ['ticket-comments', organisationId, ticketId],
    queryFn: () =>
      request<CommentPage>(`/organisations/${organisationId}/tickets/${ticketId}/comments?limit=20`),
  })
  const timeline = useQuery({
    queryKey: ['ticket-timeline', organisationId, ticketId],
    queryFn: () =>
      request<TimelinePage>(`/organisations/${organisationId}/tickets/${ticketId}/timeline?limit=20`),
  })
  const attachments = useQuery({
    queryKey: ['ticket-attachments', organisationId, ticketId],
    queryFn: () =>
      request<AttachmentItem[]>(`/organisations/${organisationId}/tickets/${ticketId}/attachments`),
  })
  const uploadAttachment = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      const response = await fetch(`/api/v1/organisations/${organisationId}/tickets/${ticketId}/attachments`, {
        method: 'POST',
        body: formData,
        credentials: 'include',
        headers: {
          'X-CSRF-Token': readCookie('rh_csrf') || '',
        },
      })
      if (!response.ok) throw new Error('Attachment upload failed.')
      return response.json()
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['ticket-attachments', organisationId, ticketId] }),
        queryClient.invalidateQueries({ queryKey: ['ticket-timeline', organisationId, ticketId] }),
      ])
    },
  })
  const deleteAttachment = useMutation({
    mutationFn: (attachmentId: string) =>
      request(`/organisations/${organisationId}/tickets/${ticketId}/attachments/${attachmentId}`, {
        method: 'DELETE',
      }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['ticket-attachments', organisationId, ticketId] }),
        queryClient.invalidateQueries({ queryKey: ['ticket-timeline', organisationId, ticketId] }),
      ])
    },
  })
  const assignmentCandidates = useQuery({
    queryKey: ['assignment-candidates', organisationId],
    queryFn: () =>
      request<AssignmentCandidate[]>(
        `/organisations/${organisationId}/tickets/assignment-candidates`,
      ),
    enabled: permissionSet.has('ticket:assign'),
  })
  const addComment = useMutation({
    mutationFn: ({ body, kind }: { body: string; kind: 'PUBLIC' | 'INTERNAL' }) =>
      request<Comment>(`/organisations/${organisationId}/tickets/${ticketId}/comments`, {
        method: 'POST',
        body: JSON.stringify({ kind, body }),
      }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['ticket-comments', organisationId, ticketId] }),
        queryClient.invalidateQueries({ queryKey: ['ticket-timeline', organisationId, ticketId] }),
      ])
    },
  })
  const assignTicket = useMutation({
    mutationFn: ({ assignedAgentId, version }: { assignedAgentId: string; version: number }) =>
      request<TicketDetailRecord>(`/organisations/${organisationId}/tickets/${ticketId}/assignment`, {
        method: 'POST',
        body: JSON.stringify({ assigned_agent_id: assignedAgentId, version }),
      }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['ticket', organisationId, ticketId] }),
        queryClient.invalidateQueries({ queryKey: ['tickets', organisationId] }),
        queryClient.invalidateQueries({ queryKey: ['ticket-timeline', organisationId, ticketId] }),
      ])
    },
  })
  const transition = useMutation({
    mutationFn: ({ status, version, reason }: { status: string; version: number; reason?: string }) =>
      request<TicketDetailRecord>(`/organisations/${organisationId}/tickets/${ticketId}/transitions`, {
        method: 'POST',
        body: JSON.stringify({ status, version, ...(reason ? { reason } : {}) }),
      }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['ticket', organisationId, ticketId] }),
        queryClient.invalidateQueries({ queryKey: ['tickets', organisationId] }),
        queryClient.invalidateQueries({ queryKey: ['ticket-timeline', organisationId, ticketId] }),
      ])
    },
  })

  function submitComment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    addComment.mutate(
      { body: commentBody, kind: commentKind },
      { onSuccess: () => setCommentBody('') },
    )
  }

  function submitTransition(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const values = new FormData(event.currentTarget)
    const status = String(values.get('status'))
    const reason = String(values.get('reason') || '').trim()
    transition.mutate({ status, version: detail.data!.version, ...(reason ? { reason } : {}) })
  }

  if (detail.isPending || comments.isPending || timeline.isPending) {
    return <p className="section-message" role="status">Loading request detail…</p>
  }
  if (detail.isError || comments.isError || timeline.isError) {
    return <div className="form-error organisation-state" role="alert">Request detail could not be loaded.</div>
  }

  const ticket = detail.data
  const assignedAgent = assignmentCandidates.data?.find(
    (candidate) => candidate.user_id === ticket.assigned_agent_id,
  )
  const allowedTransitions = (transitions[ticket.status] ?? []).filter((status) =>
    permissionSet.has(transitionPermission(status)),
  )
  const canTransition = allowedTransitions.length > 0
  const selectedTransition = allowedTransitions.includes(transitionStatus)
    ? transitionStatus
    : (allowedTransitions[0] ?? '')
  return (
    <section className="request-detail" aria-labelledby="ticket-detail-title">
      <button className="detail-back" type="button" onClick={onBack}>
        <ArrowLeft size={16} /> Back to requests
      </button>

      <header className="detail-header">
        <div>
          <span className="ticket-number">{ticket.ticket_number}</span>
          <h2 id="ticket-detail-title">{ticket.title}</h2>
        </div>
        <div className="detail-badges">
          <span className={`badge badge-status status-${ticket.status.toLowerCase()}`}>
            <span className="badge-dot" />
            {readable(ticket.status)}
          </span>
          <span className={`badge badge-status priority-${ticket.priority.toLowerCase()}`}>
            {ticket.priority}
          </span>
        </div>
      </header>

      <p className="detail-description">{ticket.description}</p>

      <dl className="ticket-facts">
        <div><dt>SLA state</dt><dd>{readable(ticket.sla_state)}</dd></div>
        <div><dt>Created</dt><dd>{new Date(ticket.created_at).toLocaleString()}</dd></div>
        <div>
          <dt>Resolution target</dt>
          <dd>{ticket.resolution_deadline ? new Date(ticket.resolution_deadline).toLocaleString() : 'Not assigned'}</dd>
        </div>
        <div><dt>Assigned agent</dt><dd>{ticket.assigned_agent_id === user?.id ? 'You' : assignedAgent?.display_name ?? (ticket.assigned_agent_id ? 'Another agent' : 'Unassigned')}</dd></div>
      </dl>

      {(permissionSet.has('ticket:assign') || canTransition) && (
        <section className="agent-actions" aria-labelledby="agent-actions-title">
          <div>
            <p className="card-label">Controlled operations</p>
            <h3 id="agent-actions-title">Agent actions</h3>
          </div>
          {permissionSet.has('ticket:assign') && !assignmentCandidates.isPending && (
            <form className="transition-form" onSubmit={(event) => {
              event.preventDefault()
              const data = new FormData(event.currentTarget)
              assignTicket.mutate({
                assignedAgentId: String(data.get('assigned_agent_id')),
                version: ticket.version,
              })
            }}>
              <label>
                <span>Assign agent</span>
                <select
                  name="assigned_agent_id"
                  defaultValue={ticket.assigned_agent_id ?? user?.id ?? ''}
                  disabled={assignmentCandidates.isPending}
                  required
                >
                  {(assignmentCandidates.data ?? []).map((candidate) => (
                    <option key={candidate.user_id} value={candidate.user_id}>
                      {candidate.user_id === user?.id ? `${candidate.display_name} (you)` : candidate.display_name}
                    </option>
                  ))}
                </select>
              </label>
              <button
                className="btn-secondary"
                type="submit"
                disabled={assignTicket.isPending || assignmentCandidates.isPending}
              >
                {assignTicket.isPending ? 'Assigning…' : 'Assign selected agent'}
              </button>
            </form>
          )}
          {canTransition && (
            <form className="transition-form" onSubmit={submitTransition}>
              <label>
                <span>Next status</span>
                <select
                  name="status"
                  value={selectedTransition}
                  onChange={(event) => setTransitionStatus(event.target.value)}
                  required
                >
                  {allowedTransitions.map((status) => (
                    <option key={status} value={status}>{readable(status)}</option>
                  ))}
                </select>
              </label>
              {reasonRequired.has(selectedTransition) && (
                <label><span>Reason</span><input name="reason" minLength={2} maxLength={500} required /></label>
              )}
              <button className="btn-primary" type="submit" disabled={transition.isPending}>
                {transition.isPending ? 'Updating…' : 'Update status'}
              </button>
            </form>
          )}
          {(assignTicket.isError || assignmentCandidates.isError || transition.isError) && (
            <div className="form-error" role="alert">The ticket changed or this operation is not allowed. Refresh and try again.</div>
          )}
        </section>
      )}

      <AiReviewPanel
        organisationId={organisationId}
        ticketId={ticketId}
        permissions={permissions}
      />

      <section className="attachments-section" aria-labelledby="attachments-title">
        <h3 id="attachments-title">Attachments</h3>
        {permissionSet.has('attachment:create') && (
          <form
            className="attachment-upload-form"
            onSubmit={(e) => {
              e.preventDefault()
              const fileInput = e.currentTarget.elements.namedItem('file') as HTMLInputElement
              if (fileInput?.files?.[0]) {
                uploadAttachment.mutate(fileInput.files[0], {
                  onSuccess: () => {
                    fileInput.value = ''
                  },
                })
              }
            }}
          >
            <label className="file-input-label">
              <span>Upload file (PDF, PNG, JPG, TXT up to 10MB)</span>
              <input type="file" name="file" accept=".pdf,.png,.jpg,.jpeg,.txt" required />
            </label>
            <button className="btn-secondary" type="submit" disabled={uploadAttachment.isPending}>
              {uploadAttachment.isPending ? 'Uploading…' : 'Upload'}
            </button>
            {uploadAttachment.isError && (
              <div className="form-error" role="alert">File upload failed. Check file size and type.</div>
            )}
          </form>
        )}

        <div className="attachments-list">
          {attachments.isPending ? (
            <p className="muted">Loading attachments…</p>
          ) : (attachments.data?.length ?? 0) === 0 ? (
            <p className="muted">No attachments uploaded yet.</p>
          ) : (
            <ul className="attachment-items">
              {(attachments.data ?? []).map((att) => (
                <li key={att.id} className="attachment-item">
                  <div className="attachment-info">
                    <strong className="attachment-name">{att.original_filename}</strong>
                    <small className="muted">
                      {(att.size_bytes / 1024).toFixed(1)} KB · Scan: {att.scan_status}
                    </small>
                  </div>
                  <div className="attachment-actions">
                    <a
                      className="btn-ghost btn-sm"
                      href={`/api/v1/organisations/${organisationId}/tickets/${ticketId}/attachments/${att.id}/download`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Download
                    </a>
                    <button
                      className="btn-ghost btn-sm danger-text"
                      type="button"
                      onClick={() => deleteAttachment.mutate(att.id)}
                      disabled={deleteAttachment.isPending}
                    >
                      Delete
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      <div className="conversation-layout">
        <section aria-labelledby="conversation-title">
          <h3 id="conversation-title">
            {permissionSet.has('internal_note:read') ? 'Conversation and internal notes' : 'Public conversation'}
          </h3>
          <form className="comment-form compact-form" onSubmit={submitComment}>
            {permissionSet.has('internal_note:create') && (
              <label>
                <span>Reply type</span>
                <select
                  name="kind"
                  value={commentKind}
                  onChange={(event) => setCommentKind(event.target.value as 'PUBLIC' | 'INTERNAL')}
                >
                  <option value="PUBLIC">Public reply</option>
                  <option value="INTERNAL">Internal note</option>
                </select>
              </label>
            )}
            <label>
              <span>Add a reply</span>
              <textarea
                name="body"
                value={commentBody}
                onChange={(event) => setCommentBody(event.target.value)}
                minLength={1}
                maxLength={10_000}
                rows={3}
                required
              />
            </label>
            {addComment.isError && <div className="form-error" role="alert">Your reply could not be added.</div>}
            <button className="btn-primary" type="submit" disabled={addComment.isPending}>
              {addComment.isPending ? 'Posting…' : 'Post reply'}
            </button>
          </form>
          <div className="comment-list" aria-live="polite">
            {comments.data.items.length === 0 ? (
              <p className="muted">No public replies yet.</p>
            ) : comments.data.items.map((comment) => (
              <article className={`comment ${comment.kind === 'INTERNAL' ? 'internal-comment' : ''}`} key={comment.id}>
                <div>
                  <strong>{comment.author_id === user?.id ? 'You' : 'Team member'}{comment.kind === 'INTERNAL' ? ' · Internal note' : ''}</strong>
                  <time dateTime={comment.created_at}>{new Date(comment.created_at).toLocaleString()}</time>
                </div>
                <p>{comment.body}</p>
              </article>
            ))}
          </div>
        </section>

        <aside className="timeline" aria-labelledby="timeline-title">
          <h3 id="timeline-title">Timeline</h3>
          <ol>
            {timeline.data.items.map((event) => (
              <li key={event.id}>
                <span>{readable(event.event_type)}</span>
                <small>{new Date(event.created_at).toLocaleString()}</small>
              </li>
            ))}
          </ol>
        </aside>
      </div>
    </section>
  )
}
