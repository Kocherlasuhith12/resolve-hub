import { useState, type FormEvent } from 'react'
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { List, Columns3 } from 'lucide-react'
import { useAuth } from '../../auth/useAuth'
import { TicketDetail } from './TicketDetail'
import { TicketKanbanView } from './TicketKanbanView'
import { TicketDrawer } from './TicketDrawer'

type Category = {
  id: string
  name: string
  description: string | null
  default_priority: string
  is_active: boolean
}

type Department = { id: string }

type Ticket = {
  id: string
  ticket_number: string
  title: string
  description: string
  priority: string
  status: string
  created_at: string
}

type TicketPage = { items: Ticket[]; next_cursor: string | null }

type MembershipContext = {
  role_name: string
  permissions: string[]
}

function readable(value: string): string {
  return value.replaceAll('_', ' ').toLowerCase().replace(/^./, (l) => l.toUpperCase())
}

export function TicketWorkspace({ organisationId }: { organisationId: string }) {
  const { request } = useAuth()
  const queryClient = useQueryClient()
  const [setupError, setSetupError] = useState<string | null>(null)
  const [ticketError, setTicketError] = useState<string | null>(null)
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null)
  const [drawerTicketId, setDrawerTicketId] = useState<string | null>(null)
  const [searchInput, setSearchInput] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [priorityFilter, setPriorityFilter] = useState('')
  const [displayMode, setDisplayMode] = useState<'list' | 'kanban'>('list')

  const membership = useQuery({
    queryKey: ['membership', organisationId],
    queryFn: () =>
      request<MembershipContext>(`/organisations/${organisationId}/membership/me`),
    enabled: Boolean(organisationId),
  })

  const categories = useQuery({
    queryKey: ['categories', organisationId],
    queryFn: () => request<Category[]>(`/organisations/${organisationId}/categories`),
    enabled: Boolean(organisationId),
  })

  const tickets = useInfiniteQuery({
    queryKey: ['tickets', organisationId, statusFilter, priorityFilter],
    initialPageParam: null as string | null,
    queryFn: ({ pageParam }) => {
      const query = new URLSearchParams({ limit: '50' })
      if (statusFilter) query.set('status', statusFilter)
      if (priorityFilter) query.set('priority', priorityFilter)
      if (pageParam) query.set('cursor', pageParam)
      return request<TicketPage>(`/organisations/${organisationId}/tickets?${query}`)
    },
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    enabled: Boolean(organisationId),
  })

  const search = useQuery({
    queryKey: ['ticket-search', organisationId, searchQuery],
    queryFn: () => {
      const query = new URLSearchParams({ query: searchQuery, limit: '50' })
      return request<TicketPage>(`/organisations/${organisationId}/search/tickets?${query}`)
    },
    enabled: searchQuery.length >= 2,
  })

  const serviceSetup = useMutation({
    mutationFn: async (payload: {
      departmentName: string
      categoryName: string
      defaultPriority: string
    }) => {
      const department = await request<Department>(
        `/organisations/${organisationId}/departments`,
        { method: 'POST', body: JSON.stringify({ name: payload.departmentName }) },
      )
      return request<Category>(`/organisations/${organisationId}/categories`, {
        method: 'POST',
        body: JSON.stringify({
          department_id: department.id,
          name: payload.categoryName,
          default_priority: payload.defaultPriority,
        }),
      })
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['categories', organisationId] })
    },
    onError: () => setSetupError('The service category could not be configured.'),
  })

  const createTicket = useMutation({
    mutationFn: (payload: {
      category_id: string
      title: string
      description: string
      priority?: string
      source: 'WEB'
    }) =>
      request<Ticket>(`/organisations/${organisationId}/tickets`, {
        method: 'POST',
        headers: { 'Idempotency-Key': crypto.randomUUID() },
        body: JSON.stringify(payload),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['tickets', organisationId] })
    },
    onError: () => setTicketError('The request could not be submitted. Review it and try again.'),
  })

  const categoryItems = (categories.data ?? []).filter((category) => category.is_active)
  const ticketItems = searchQuery
    ? (search.data?.items ?? [])
    : (tickets.data?.pages.flatMap((page) => page.items) ?? [])

  function submitServiceSetup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSetupError(null)
    const values = new FormData(event.currentTarget)
    serviceSetup.mutate({
      departmentName: String(values.get('department_name')),
      categoryName: String(values.get('category_name')),
      defaultPriority: String(values.get('default_priority')),
    })
  }

  function submitTicket(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setTicketError(null)
    const form = event.currentTarget
    const values = new FormData(form)
    const priority = String(values.get('priority'))
    createTicket.mutate(
      {
        category_id: String(values.get('category_id')),
        title: String(values.get('title')),
        description: String(values.get('description')),
        ...(priority ? { priority } : {}),
        source: 'WEB',
      },
      { onSuccess: () => form.reset() },
    )
  }

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const normalized = searchInput.trim()
    if (normalized.length >= 2) setSearchQuery(normalized)
  }

  if (categories.isPending || tickets.isPending || membership.isPending) {
    return <p className="section-message" role="status">Loading service requests…</p>
  }

  if (categories.isError || tickets.isError || membership.isError) {
    return <div className="form-error organisation-state" role="alert">Service requests could not be loaded.</div>
  }

  if (categoryItems.length === 0) {
    return (
      <section className="service-setup" aria-labelledby="service-setup-title">
        <div>
          <p className="card-label">Service catalogue</p>
          <h2 id="service-setup-title">Configure the first service</h2>
          <p>Tickets require an authorised department and category. Set up both to begin.</p>
        </div>
        <form className="compact-form" onSubmit={submitServiceSetup}>
          <label>
            <span>Department name</span>
            <input name="department_name" minLength={2} maxLength={120} required />
          </label>
          <label>
            <span>Service category</span>
            <input name="category_name" minLength={2} maxLength={120} required />
          </label>
          <label>
            <span>Default priority</span>
            <select name="default_priority" defaultValue="MEDIUM">
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
              <option value="CRITICAL">Critical</option>
            </select>
          </label>
          {setupError && <div className="form-error" role="alert">{setupError}</div>}
          <button className="primary-button" type="submit" disabled={serviceSetup.isPending}>
            {serviceSetup.isPending ? 'Configuring…' : 'Configure service'}
            {!serviceSetup.isPending && <span aria-hidden="true">→</span>}
          </button>
        </form>
      </section>
    )
  }

  if (selectedTicketId) {
    return (
      <TicketDetail
        organisationId={organisationId}
        ticketId={selectedTicketId}
        permissions={membership.data.permissions}
        onBack={() => setSelectedTicketId(null)}
      />
    )
  }

  const isStaff = membership.data.permissions.includes('ticket:read_all')

  return (
    <section aria-labelledby="requests-title">
      {/* Drawer Inspector */}
      <TicketDrawer
        isOpen={Boolean(drawerTicketId)}
        organisationId={organisationId}
        ticketId={drawerTicketId}
        permissions={membership.data.permissions}
        onClose={() => setDrawerTicketId(null)}
      />

      {/* Page Header */}
      <div className="page-header-row">
        <div className="page-header">
          <h1 id="requests-title">{isStaff ? 'Agent queue' : 'Service Requests'}</h1>
          <p className="page-subtitle">{isStaff ? 'Manage and triage incoming requests' : 'Submit and track your requests'}</p>
        </div>
        <div className="view-toggle">
          <button
            className={`view-toggle-btn ${displayMode === 'list' ? 'active' : ''}`}
            type="button"
            onClick={() => setDisplayMode('list')}
          >
            <List size={14} /> List
          </button>
          <button
            className={`view-toggle-btn ${displayMode === 'kanban' ? 'active' : ''}`}
            type="button"
            onClick={() => setDisplayMode('kanban')}
          >
            <Columns3 size={14} /> Board
          </button>
        </div>
      </div>

      {/* Toolbar */}
      <div className="ticket-toolbar">
        <form role="search" onSubmit={submitSearch} style={{ display: 'flex', gap: 8, flex: 1 }}>
          <label style={{ display: 'flex', gap: 8, flex: 1, alignItems: 'center' }}>
            <span className="sr-only">Search requests</span>
            <input
              className="ticket-search-input"
              type="search"
              aria-label="Search requests"
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder="Search tickets…"
              minLength={2}
              maxLength={200}
            />
          </label>
          <button className="btn-secondary btn-sm" type="submit">Search</button>
          {searchQuery && (
            <button
              className="btn-ghost btn-sm"
              type="button"
              onClick={() => { setSearchInput(''); setSearchQuery('') }}
            >
              Clear
            </button>
          )}
        </form>
        {search.isError && <div className="form-error search-error" role="alert">Search could not be completed.</div>}

        {isStaff && (
          <>
            <select
              className="filter-select"
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
            >
              <option value="">All statuses</option>
              {['SUBMITTED', 'TRIAGED', 'ASSIGNED', 'IN_PROGRESS', 'WAITING_FOR_REQUESTER', 'ESCALATED', 'RESOLVED', 'CLOSED', 'CANCELLED'].map((status) => (
                <option key={status} value={status}>{status.replaceAll('_', ' ')}</option>
              ))}
            </select>
            <select
              className="filter-select"
              value={priorityFilter}
              onChange={(event) => setPriorityFilter(event.target.value)}
            >
              <option value="">All priorities</option>
              {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map((priority) => (
                <option key={priority} value={priority}>{priority}</option>
              ))}
            </select>
          </>
        )}
      </div>

      {displayMode === 'kanban' ? (
        <TicketKanbanView
          organisationId={organisationId}
          tickets={ticketItems}
          onSelectTicket={(ticketId) => setSelectedTicketId(ticketId)}
        />
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 24 }}>
          {/* Data Table */}
          <div className="ticket-table-wrap">
            {ticketItems.length === 0 ? (
              <div className="empty-state">
                <h3>No requests found</h3>
                <p>Submitted requests will appear in this queue.</p>
              </div>
            ) : (
              <table className="ticket-table">
                <thead>
                  <tr>
                    <th>Ticket ID</th>
                    <th>Title</th>
                    <th>Priority</th>
                    <th>Status</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {ticketItems.map((ticket) => (
                    <tr key={ticket.id}>
                      <td>
                        <span className="ticket-number">{ticket.ticket_number}</span>
                      </td>
                      <td>
                        <h3 className="ticket-title-heading">
                          <button
                            className="ticket-title-btn"
                            type="button"
                            onClick={() => setSelectedTicketId(ticket.id)}
                          >
                            {ticket.title}
                          </button>
                        </h3>
                      </td>
                      <td>
                        <span className={`badge badge-status priority-${ticket.priority.toLowerCase()}`}>
                          {ticket.priority}
                        </span>
                      </td>
                      <td>
                        <span className={`badge badge-status status-${ticket.status.toLowerCase()}`}>
                          <span className="badge-dot" />
                          {readable(ticket.status)}
                        </span>
                      </td>
                      <td>
                        <time dateTime={ticket.created_at}>
                          {new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(new Date(ticket.created_at))}
                        </time>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            {tickets.hasNextPage && (
              <div style={{ padding: 16, textAlign: 'center' }}>
                <button
                  className="btn-secondary btn-sm"
                  type="button"
                  disabled={tickets.isFetchingNextPage}
                  onClick={() => void tickets.fetchNextPage()}
                >
                  {tickets.isFetchingNextPage ? 'Loading…' : 'Load more requests'}
                </button>
              </div>
            )}
          </div>

          {/* Submit Form */}
          <div className="card">
            <form className="compact-form" onSubmit={submitTicket}>
              <h3>Submit a request</h3>
              <label>
                <span>Category</span>
                <select name="category_id" required defaultValue="">
                  <option value="" disabled>Select a service</option>
                  {categoryItems.map((category) => (
                    <option key={category.id} value={category.id}>{category.name}</option>
                  ))}
                </select>
              </label>
              <label>
                <span>Title</span>
                <input name="title" minLength={3} maxLength={200} required />
              </label>
              <label>
                <span>Description</span>
                <textarea name="description" minLength={3} maxLength={20_000} rows={5} required />
              </label>
              <label>
                <span>Priority</span>
                <select name="priority" defaultValue="">
                  <option value="">Category default</option>
                  <option value="LOW">Low</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HIGH">High</option>
                  <option value="CRITICAL">Critical</option>
                </select>
              </label>
              {ticketError && <div className="form-error" role="alert">{ticketError}</div>}
              <button className="primary-button" type="submit" disabled={createTicket.isPending}>
                {createTicket.isPending ? 'Submitting…' : 'Submit request'}
                {!createTicket.isPending && <span aria-hidden="true">→</span>}
              </button>
            </form>
          </div>
        </div>
      )}
    </section>
  )
}
