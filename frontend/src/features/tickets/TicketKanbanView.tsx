import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../../auth/useAuth'

type Ticket = {
  id: string
  ticket_number: string
  title: string
  description: string
  priority: string
  status: string
  created_at: string
}

const columns = [
  { id: 'SUBMITTED', title: 'New', statuses: ['SUBMITTED'] },
  { id: 'TRIAGED', title: 'Triaged', statuses: ['TRIAGED', 'ASSIGNED'] },
  { id: 'IN_PROGRESS', title: 'In Progress', statuses: ['IN_PROGRESS', 'ESCALATED'] },
  { id: 'WAITING', title: 'Waiting', statuses: ['WAITING_FOR_REQUESTER'] },
  { id: 'RESOLVED', title: 'Resolved', statuses: ['RESOLVED', 'CLOSED'] },
]

export function TicketKanbanView({
  organisationId,
  tickets,
  onSelectTicket,
}: {
  organisationId: string
  tickets: Ticket[]
  onSelectTicket: (ticketId: string) => void
}) {
  const { request } = useAuth()
  const queryClient = useQueryClient()

  const transitionTicket = useMutation({
    mutationFn: (payload: { ticketId: string; nextStatus: string }) =>
      request<Ticket>(`/organisations/${organisationId}/tickets/${payload.ticketId}/status`, {
        method: 'POST',
        headers: { 'Idempotency-Key': crypto.randomUUID() },
        body: JSON.stringify({ to_status: payload.nextStatus }),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['tickets', organisationId] })
    },
  })

  return (
    <div className="kanban-board">
      {columns.map((col) => {
        const colTickets = tickets.filter((t) => col.statuses.includes(t.status))
        return (
          <div className="kanban-column" key={col.id}>
            <div className="kanban-col-header">
              <h3>{col.title}</h3>
              <span className="kanban-col-count">{colTickets.length}</span>
            </div>
            <div className="kanban-cards-stack">
              {colTickets.length === 0 ? (
                <div className="kanban-empty">No items in stage</div>
              ) : (
                colTickets.map((t) => (
                  <div className="kanban-card" key={t.id}>
                    <div className="kanban-card-top">
                      <span className="ticket-number">{t.ticket_number}</span>
                      <span className={`badge badge-status priority-${t.priority.toLowerCase()}`} style={{ fontSize: 11 }}>
                        {t.priority}
                      </span>
                    </div>
                    <h4 className="kanban-card-title">
                      <button type="button" onClick={() => onSelectTicket(t.id)}>
                        {t.title}
                      </button>
                    </h4>
                    <p className="kanban-card-desc">{t.description}</p>
                    <div className="kanban-card-actions">
                      {col.id === 'SUBMITTED' && (
                        <button
                          className="btn-secondary btn-sm"
                          disabled={transitionTicket.isPending}
                          onClick={() => transitionTicket.mutate({ ticketId: t.id, nextStatus: 'TRIAGED' })}
                        >
                          Triage
                        </button>
                      )}
                      {col.id === 'TRIAGED' && (
                        <button
                          className="btn-secondary btn-sm"
                          disabled={transitionTicket.isPending}
                          onClick={() => transitionTicket.mutate({ ticketId: t.id, nextStatus: 'IN_PROGRESS' })}
                        >
                          Start
                        </button>
                      )}
                      {col.id === 'IN_PROGRESS' && (
                        <button
                          className="btn-primary btn-sm"
                          disabled={transitionTicket.isPending}
                          onClick={() => transitionTicket.mutate({ ticketId: t.id, nextStatus: 'RESOLVED' })}
                        >
                          Resolve
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
