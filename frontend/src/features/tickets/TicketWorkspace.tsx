import { useState, type FormEvent } from 'react'
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../../auth/useAuth'
import { TicketDetail } from './TicketDetail'

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

export function TicketWorkspace({ organisationId }: { organisationId: string }) {
  const { request } = useAuth()
  const queryClient = useQueryClient()
  const [setupError, setSetupError] = useState<string | null>(null)
  const [ticketError, setTicketError] = useState<string | null>(null)
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null)
  const [searchInput, setSearchInput] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [priorityFilter, setPriorityFilter] = useState('')
  const membership = useQuery({
    queryKey: ['membership', organisationId],
    queryFn: () =>
      request<MembershipContext>(`/organisations/${organisationId}/membership/me`),
  })
  const categories = useQuery({
    queryKey: ['categories', organisationId],
    queryFn: () => request<Category[]>(`/organisations/${organisationId}/categories`),
  })
  const tickets = useInfiniteQuery({
    queryKey: ['tickets', organisationId, statusFilter, priorityFilter],
    initialPageParam: null as string | null,
    queryFn: ({ pageParam }) => {
      const query = new URLSearchParams({ limit: '20' })
      if (statusFilter) query.set('status', statusFilter)
      if (priorityFilter) query.set('priority', priorityFilter)
      if (pageParam) query.set('cursor', pageParam)
      return request<TicketPage>(`/organisations/${organisationId}/tickets?${query}`)
    },
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
  })
  const search = useQuery({
    queryKey: ['ticket-search', organisationId, searchQuery],
    queryFn: () => {
      const query = new URLSearchParams({ query: searchQuery, limit: '20' })
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
  const ticketItems = searchQuery ? (search.data?.items ?? []) : (tickets.data?.pages.flatMap((page) => page.items) ?? [])

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
    <section className="ticket-workspace" aria-labelledby="requests-title">
      <div className="ticket-heading">
        <div>
          <p className="card-label">{isStaff ? membership.data.role_name : 'Requester workspace'}</p>
          <h2 id="requests-title">{isStaff ? 'Agent queue' : 'Service requests'}</h2>
        </div>
        <span>{ticketItems.length} loaded</span>
      </div>

      <form className="ticket-search" role="search" onSubmit={submitSearch}>
        <label>
          <span className="sr-only">Search requests</span>
          <input
            type="search"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="Search requests and public replies"
            minLength={2}
            maxLength={200}
          />
        </label>
        <button className="quiet-button" type="submit">Search</button>
        {searchQuery && (
          <button
            className="text-button"
            type="button"
            onClick={() => { setSearchInput(''); setSearchQuery('') }}
          >
            Clear search
          </button>
        )}
      </form>
      {search.isError && <div className="form-error search-error" role="alert">Search could not be completed.</div>}

      {isStaff && (
        <div className="queue-filters" aria-label="Queue filters">
          <label>
            <span>Status</span>
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              <option value="">All statuses</option>
              {['SUBMITTED', 'TRIAGED', 'ASSIGNED', 'IN_PROGRESS', 'WAITING_FOR_REQUESTER', 'ESCALATED', 'RESOLVED', 'CLOSED', 'CANCELLED'].map((status) => (
                <option key={status} value={status}>{status.replaceAll('_', ' ')}</option>
              ))}
            </select>
          </label>
          <label>
            <span>Priority</span>
            <select value={priorityFilter} onChange={(event) => setPriorityFilter(event.target.value)}>
              <option value="">All priorities</option>
              {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map((priority) => (
                <option key={priority} value={priority}>{priority}</option>
              ))}
            </select>
          </label>
        </div>
      )}

      <div className="ticket-layout">
        <form className="ticket-form compact-form" onSubmit={submitTicket}>
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

        <div className="ticket-list" aria-live="polite">
          {ticketItems.length === 0 ? (
            <div className="empty-tickets">
              <h3>No requests yet</h3>
              <p>Your submitted requests will appear here.</p>
            </div>
          ) : ticketItems.map((ticket) => (
            <article className="ticket-card" key={ticket.id}>
              <div>
                <span className="ticket-number">{ticket.ticket_number}</span>
                <span className={`priority-badge priority-${ticket.priority.toLowerCase()}`}>
                  {ticket.priority}
                </span>
              </div>
              <h3>
                <button className="ticket-title-button" type="button" onClick={() => setSelectedTicketId(ticket.id)}>
                  {ticket.title}
                </button>
              </h3>
              <p>{ticket.description}</p>
              <footer>
                <span>{ticket.status.replaceAll('_', ' ')}</span>
                <time dateTime={ticket.created_at}>
                  {new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(new Date(ticket.created_at))}
                </time>
              </footer>
            </article>
          ))}
          {tickets.hasNextPage && (
            <button
              className="quiet-button load-more"
              type="button"
              disabled={tickets.isFetchingNextPage}
              onClick={() => void tickets.fetchNextPage()}
            >
              {tickets.isFetchingNextPage ? 'Loading…' : 'Load more requests'}
            </button>
          )}
        </div>
      </div>
    </section>
  )
}
