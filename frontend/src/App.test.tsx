import { cleanup, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useState } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import { AuthProvider } from './auth/AuthProvider'
import { useAuth } from './auth/useAuth'

function response(body: unknown, status = 200): Response {
  return new Response(status === 204 ? null : JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function renderApp(path: string) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[path]}>
        <AuthProvider><App /></AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function RefreshHarness() {
  const { login, request, status } = useAuth()
  const [result, setResult] = useState('idle')

  async function run() {
    try {
      await login('alex@example.com', 'Long secure password 123!')
      const values = await Promise.all([
        request<{ value: string }>('/protected/one'),
        request<{ value: string }>('/protected/two'),
      ])
      setResult(values.map((item) => item.value).join(','))
    } catch {
      setResult('failed')
    }
  }

  return (
    <>
      <button type="button" onClick={() => void run()}>Run protected requests</button>
      <output>{status}:{result}</output>
    </>
  )
}

function renderRefreshHarness() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const rendered = render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider><RefreshHarness /></AuthProvider>
    </QueryClientProvider>,
  )
  return { ...rendered, queryClient }
}

describe('authentication shell', () => {
  afterEach(() => {
    cleanup()
    vi.unstubAllGlobals()
    document.cookie = 'resolvehub_csrf=; Max-Age=0; path=/'
  })

  it('logs in and renders the authenticated workspace', async () => {
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        response({
          access_token: 'access-token',
          csrf_token: 'csrf-token',
          token_type: 'bearer',
          expires_in: 900,
        }),
      )
      .mockResolvedValueOnce(
        response({
          id: '436df704-2d42-4e09-91cf-d615a748878b',
          email: 'alex@example.com',
          display_name: 'Alex Morgan',
          is_email_verified: true,
          is_active: true,
        }),
      )
      .mockResolvedValueOnce(response([]))
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()

    renderApp('/login')

    await user.type(screen.getByLabelText('Email address'), 'alex@example.com')
    await user.type(screen.getByLabelText(/^Password/), 'Long secure password 123!')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('heading', { name: 'Good to see you, Alex.' })).toBeVisible()
    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      '/api/v1/auth/browser/login',
      expect.objectContaining({ credentials: 'include', method: 'POST' }),
    )
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      '/api/v1/auth/me',
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer access-token' }),
      }),
    )
  })

  it('shows the shared API error without exposing details', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn<typeof fetch>().mockResolvedValue(
        response(
          { error: { code: 'AUTHENTICATION_FAILED', message: 'Invalid email or password.' } },
          401,
        ),
      ),
    )
    const user = userEvent.setup()
    renderApp('/login')

    await user.type(screen.getByLabelText('Email address'), 'unknown@example.com')
    await user.type(screen.getByLabelText(/^Password/), 'Long secure password 123!')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid email or password.')
  })

  it('registers, verifies the email, and returns to sign in', async () => {
    const verificationToken = 'v'.repeat(48)
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        response({
          message: 'If the address can be registered, verification instructions will be sent.',
          requires_email_verification: true,
          verification_token: verificationToken,
        }, 202),
      )
      .mockResolvedValueOnce(response(null, 204))
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()

    renderApp('/register')

    await user.type(screen.getByLabelText('Full name'), 'Riya Sharma')
    await user.type(screen.getByLabelText('Email address'), 'riya@example.com')
    await user.type(screen.getByLabelText(/^Password/), 'Long secure password 123!')
    await user.type(screen.getByLabelText('Confirm password'), 'Long secure password 123!')
    await user.click(screen.getByRole('button', { name: 'Create account' }))

    expect(await screen.findByRole('heading', { name: 'Verify your email' })).toBeVisible()
    expect(screen.getByLabelText('Verification token')).toHaveValue(verificationToken)
    await user.click(screen.getByRole('button', { name: 'Verify account' }))

    expect(await screen.findByRole('status')).toHaveTextContent('Email verified')
    expect(screen.getByLabelText('Email address')).toHaveValue('riya@example.com')
    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      '/api/v1/auth/register',
      expect.objectContaining({ method: 'POST' }),
    )
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      '/api/v1/auth/verify-email',
      expect.objectContaining({ method: 'POST' }),
    )
  })

  it('rejects mismatched registration passwords before calling the API', async () => {
    const fetchMock = vi.fn<typeof fetch>()
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()
    renderApp('/register')

    await user.type(screen.getByLabelText('Full name'), 'Riya Sharma')
    await user.type(screen.getByLabelText('Email address'), 'riya@example.com')
    await user.type(screen.getByLabelText(/^Password/), 'Long secure password 123!')
    await user.type(screen.getByLabelText('Confirm password'), 'Different secure password!')
    await user.click(screen.getByRole('button', { name: 'Create account' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Passwords do not match.')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('coordinates one refresh for concurrent 401 responses and retries each request once', async () => {
    let refreshCount = 0
    const protectedAttempts = new Map<string, number>()
    const fetchMock = vi.fn<typeof fetch>(async (input, init) => {
      const path = String(input)
      if (path.endsWith('/auth/browser/login')) {
        document.cookie = 'resolvehub_csrf=csrf-token; path=/'
        return response({
          access_token: 'expired-access-token',
          csrf_token: 'csrf-token',
          token_type: 'bearer',
          expires_in: 900,
        })
      }
      if (path.endsWith('/auth/me')) {
        return response({
          id: '436df704-2d42-4e09-91cf-d615a748878b',
          email: 'alex@example.com',
          display_name: 'Alex Morgan',
          is_email_verified: true,
          is_active: true,
        })
      }
      if (path.endsWith('/auth/browser/refresh')) {
        refreshCount += 1
        await new Promise((resolve) => setTimeout(resolve, 10))
        return response({
          access_token: 'renewed-access-token',
          csrf_token: 'rotated-csrf-token',
          token_type: 'bearer',
          expires_in: 900,
        })
      }
      if (path.includes('/protected/')) {
        protectedAttempts.set(path, (protectedAttempts.get(path) ?? 0) + 1)
        const authorization = new Headers(init?.headers).get('Authorization')
        return authorization === 'Bearer renewed-access-token'
          ? response({ value: path.endsWith('/one') ? 'one' : 'two' })
          : response({ error: { code: 'ACCESS_TOKEN_INVALID', message: 'Invalid token.' } }, 401)
      }
      throw new Error(`Unexpected request: ${path}`)
    })
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()
    renderRefreshHarness()

    await user.click(screen.getByRole('button', { name: 'Run protected requests' }))

    expect(await screen.findByText('authenticated:one,two')).toBeVisible()
    expect(refreshCount).toBe(1)
    expect([...protectedAttempts.values()]).toEqual([2, 2])
    const retriedCalls = fetchMock.mock.calls.filter(([, init]) =>
      new Headers(init?.headers).get('Authorization') === 'Bearer renewed-access-token')
    expect(retriedCalls).toHaveLength(2)
  })

  it('clears the session and cached tenant data when refresh fails', async () => {
    let refreshCount = 0
    vi.stubGlobal('fetch', vi.fn<typeof fetch>(async (input) => {
      const path = String(input)
      if (path.endsWith('/auth/browser/login')) {
        document.cookie = 'resolvehub_csrf=csrf-token; path=/'
        return response({
          access_token: 'expired-access-token',
          csrf_token: 'csrf-token',
          token_type: 'bearer',
          expires_in: 900,
        })
      }
      if (path.endsWith('/auth/me')) {
        return response({
          id: '436df704-2d42-4e09-91cf-d615a748878b',
          email: 'alex@example.com',
          display_name: 'Alex Morgan',
          is_email_verified: true,
          is_active: true,
        })
      }
      if (path.endsWith('/auth/browser/refresh')) {
        refreshCount += 1
        return response({ error: { code: 'SESSION_REVOKED', message: 'Session expired.' } }, 401)
      }
      if (path.includes('/protected/')) {
        return response({ error: { code: 'ACCESS_TOKEN_INVALID', message: 'Invalid token.' } }, 401)
      }
      throw new Error(`Unexpected request: ${path}`)
    }))
    const user = userEvent.setup()
    const { queryClient } = renderRefreshHarness()
    queryClient.setQueryData(['tickets', 'sensitive-tenant'], [{ id: 'cached-ticket' }])

    await user.click(screen.getByRole('button', { name: 'Run protected requests' }))

    expect(await screen.findByText('unauthenticated:failed')).toBeVisible()
    expect(refreshCount).toBe(1)
    expect(queryClient.getQueryData(['tickets', 'sensitive-tenant'])).toBeUndefined()
  })

  it('loads the selected tenant and submits a requester ticket', async () => {
    const socketConnections: Array<{ url: string; protocols: string[] }> = []
    class FakeWebSocket {
      onopen: ((event: Event) => void) | null = null
      onmessage: ((event: MessageEvent) => void) | null = null
      onerror: ((event: Event) => void) | null = null
      onclose: ((event: CloseEvent) => void) | null = null

      constructor(url: string | URL, protocols: string | string[]) {
        socketConnections.push({
          url: String(url),
          protocols: typeof protocols === 'string' ? [protocols] : protocols,
        })
        queueMicrotask(() => this.onopen?.(new Event('open')))
      }

      close() {
        this.onclose?.(new Event('close') as CloseEvent)
      }
    }
    vi.stubGlobal('WebSocket', FakeWebSocket as unknown as typeof WebSocket)
    const ticket = {
      id: '561855ef-5e9d-47fd-aa33-e28aff23e974',
      ticket_number: 'REQ-000001',
      title: 'Water leak near reception',
      description: 'Water is leaking continuously beside the entrance.',
      priority: 'HIGH',
      status: 'SUBMITTED',
      created_at: '2026-07-18T09:00:00Z',
    }
    let created = false
    let assignedAgentId: string | null = null
    let ticketStatus = 'SUBMITTED'
    let version = 1
    const department = {
      id: 'aa3ee939-90d5-43ae-bdb7-b248dd82f45d',
      name: 'Facilities',
      description: null,
      is_active: true,
    }
    const category = {
      id: 'b2e8a418-8d73-4ce4-8b84-0961e8010e52',
      department_id: department.id,
      name: 'Building maintenance',
      description: null,
      default_priority: 'HIGH',
      is_active: true,
    }
    const departments: Array<{ id: string; name: string; description: string | null; is_active: boolean }> = [department]
    const categories = [category]
    const calendars: Array<{ id: string; name: string; timezone: string; weekly_hours: object; is_active: boolean }> = []
    const policies: Array<{ id: string; category_id: string; calendar_id: string; priority: string; first_response_minutes: number; resolution_minutes: number; warning_percent: number; pause_on_waiting: boolean; is_active: boolean }> = []
    const invitationRecords: Array<{
      id: string
      email: string
      role_id: string
      status: 'PENDING' | 'REVOKED'
      expires_at: string
      accepted_at: null
      revoked_at: string | null
      created_at: string
      invitation_token: string | null
    }> = []
    const comments: Array<{
      id: string
      author_id: string
      kind: 'PUBLIC' | 'INTERNAL'
      body: string
      created_at: string
    }> = []
    const notification = {
      id: '99d65387-d459-4a62-bfbf-e9ea0a2fc763',
      kind: 'TICKET_CREATED',
      title: 'Ticket created',
      body: 'REQ-000001 has a new ticket created event.',
      resource_type: 'ticket',
      resource_id: ticket.id,
      read_at: null as string | null,
      created_at: '2026-07-18T09:01:00Z',
    }
    const aiSuggestions: Array<{
      id: string
      run_id: string
      ticket_id: string
      kind: 'PRIORITY' | 'DUPLICATE'
      value: Record<string, unknown>
      confidence: number
      meets_threshold: boolean
      status: 'PENDING' | 'ACCEPTED' | 'REJECTED'
      decided_by_id: string | null
      decided_at: string | null
      created_at: string
    }> = []
    const fetchMock = vi.fn<typeof fetch>(async (input, init) => {
      const path = String(input)
      if (path.endsWith('/auth/browser/login')) {
        return response({
          access_token: 'access-token',
          csrf_token: 'csrf-token',
          token_type: 'bearer',
          expires_in: 900,
        })
      }
      if (path.endsWith('/auth/me')) {
        return response({
          id: '436df704-2d42-4e09-91cf-d615a748878b',
          email: 'alex@example.com',
          display_name: 'Alex Morgan',
          is_email_verified: true,
          is_active: true,
        })
      }
      if (path.endsWith('/organisations')) {
        return response([
          {
            id: '314bf529-de12-46b6-81e2-770889ff4203',
            name: 'Northstar Services',
            slug: 'northstar-services',
            is_active: true,
          },
        ])
      }
      if (path.endsWith('/membership/me')) {
        return response({
          role_name: 'Organisation Admin',
          permissions: [
            'organisation:read',
            'ticket:read_all',
            'ticket:assign',
            'ticket:transition',
            'internal_note:create',
            'internal_note:read',
            'member:invite',
            'member:read',
            'department:create',
            'category:create',
            'sla:manage',
            'notification:read',
            'ai:suggest',
            'ai:review',
          ],
        })
      }
      if (path.includes('/notifications?')) {
        return response({ items: [notification], next_cursor: null })
      }
      if (path.endsWith(`/notifications/${notification.id}/read`) && init?.method === 'POST') {
        notification.read_at = '2026-07-18T09:02:00Z'
        return response(notification)
      }
      if (path.endsWith(`/tickets/${ticket.id}/ai/suggestions`) && init?.method === 'POST') {
        aiSuggestions.push(
          {
            id: '0f67f3e6-3ed2-4fb0-8765-a03c0dd3fb5c',
            run_id: '16871c87-58e3-4459-807e-9a12f94c62f3',
            ticket_id: ticket.id,
            kind: 'PRIORITY',
            value: { priority: 'CRITICAL' },
            confidence: 0.82,
            meets_threshold: true,
            status: 'PENDING',
            decided_by_id: null,
            decided_at: null,
            created_at: '2026-07-18T09:03:00Z',
          },
          {
            id: 'ce3a0751-9e5a-432f-99da-27d85afe514b',
            run_id: '16871c87-58e3-4459-807e-9a12f94c62f3',
            ticket_id: ticket.id,
            kind: 'DUPLICATE',
            value: { ticket_ids: [] },
            confidence: 0.2,
            meets_threshold: false,
            status: 'PENDING',
            decided_by_id: null,
            decided_at: null,
            created_at: '2026-07-18T09:03:00Z',
          },
        )
        return response({
          id: '16871c87-58e3-4459-807e-9a12f94c62f3',
          status: 'SUCCEEDED',
          provider: 'fake',
          model_name: 'deterministic-rules-v1',
          prompt_version: 'phase4-v1',
          latency_ms: 1,
          suggestions: aiSuggestions,
        })
      }
      if (path.endsWith(`/tickets/${ticket.id}/ai/suggestions`)) {
        return response({ items: aiSuggestions })
      }
      const decision = path.match(/\/ai\/suggestions\/([^/]+)\/decision$/)
      if (decision && init?.method === 'POST') {
        const suggestion = aiSuggestions.find((item) => item.id === decision[1])!
        const payload = JSON.parse(String(init.body)) as { status: 'ACCEPTED' | 'REJECTED' }
        suggestion.status = payload.status
        suggestion.decided_by_id = '436df704-2d42-4e09-91cf-d615a748878b'
        suggestion.decided_at = '2026-07-18T09:04:00Z'
        return response(suggestion)
      }
      if (path.endsWith('/roles')) {
        return response([{ id: '06157045-c977-4c99-96cc-f5c05efce053', name: 'Agent', permissions: [] }])
      }
      if (path.endsWith('/members')) {
        return response([{
          id: 'b67b4858-69e4-493e-ab1f-3dbe9850234c',
          user_id: '436df704-2d42-4e09-91cf-d615a748878b',
          display_name: 'Alex Morgan',
          email: 'alex@example.com',
          role_id: '06157045-c977-4c99-96cc-f5c05efce053',
          role_name: 'Organisation Admin',
          is_active: true,
          created_at: '2026-07-18T09:00:00Z',
        }])
      }
      if (path.endsWith('/invitations') && init?.method === 'POST') {
        const payload = JSON.parse(String(init.body)) as { email: string }
        const record = {
          id: crypto.randomUUID(),
          email: payload.email,
          role_id: '06157045-c977-4c99-96cc-f5c05efce053',
          status: 'PENDING' as const,
          expires_at: '2026-07-25T09:00:00Z',
          accepted_at: null,
          revoked_at: null,
          created_at: '2026-07-18T09:00:00Z',
          invitation_token: null,
        }
        invitationRecords.unshift(record)
        return response({ id: record.id, email: payload.email, expires_at: record.expires_at, invitation_token: 'i'.repeat(48) }, 201)
      }
      if (path.endsWith('/invitations')) return response(invitationRecords)
      const resendMatch = path.match(/\/invitations\/([^/]+)\/resend$/)
      if (resendMatch && init?.method === 'POST') {
        const record = invitationRecords.find((item) => item.id === resendMatch[1])!
        return response({ ...record, invitation_token: 'r'.repeat(48) })
      }
      const revokeMatch = path.match(/\/invitations\/([^/]+)\/revoke$/)
      if (revokeMatch && init?.method === 'POST') {
        const record = invitationRecords.find((item) => item.id === revokeMatch[1])!
        record.status = 'REVOKED'
        record.revoked_at = '2026-07-18T10:00:00Z'
        return response(record)
      }
      if (path.endsWith('/departments') && init?.method === 'POST') {
        const payload = JSON.parse(String(init.body)) as { name: string; description?: string }
        const createdDepartment = { id: crypto.randomUUID(), name: payload.name, description: payload.description ?? null, is_active: true }
        departments.push(createdDepartment)
        return response(createdDepartment, 201)
      }
      if (path.endsWith('/departments')) return response(departments)
      if (path.endsWith('/categories') && init?.method === 'POST') {
        const payload = JSON.parse(String(init.body)) as { department_id: string; name: string; default_priority: string }
        const createdCategory = { id: crypto.randomUUID(), ...payload, description: null, is_active: true }
        categories.push(createdCategory)
        return response(createdCategory, 201)
      }
      if (path.endsWith('/categories')) return response(categories)
      if (path.endsWith('/sla/calendars') && init?.method === 'POST') {
        const payload = JSON.parse(String(init.body)) as { name: string; timezone: string; weekly_hours: object }
        const calendar = { id: crypto.randomUUID(), ...payload, is_active: true }
        calendars.push(calendar)
        return response(calendar, 201)
      }
      if (path.endsWith('/sla/calendars')) return response(calendars)
      if (path.includes('/sla/calendars/') && path.endsWith('/holidays') && init?.method === 'POST') {
        return response(null, 204)
      }
      if (path.endsWith('/sla/policies') && init?.method === 'POST') {
        const payload = JSON.parse(String(init.body)) as Omit<(typeof policies)[number], 'id' | 'is_active'>
        const policy = { id: crypto.randomUUID(), ...payload, is_active: true }
        policies.push(policy)
        return response(policy, 201)
      }
      if (path.endsWith('/sla/policies')) return response(policies)
      if (path.includes('/tickets?')) {
        return response({ items: created ? [ticket] : [], next_cursor: null })
      }
      if (path.includes('/search/tickets?')) {
        return response({ items: [ticket], next_cursor: null })
      }
      if (path.endsWith('/tickets') && init?.method === 'POST') {
        created = true
        return response(ticket, 201)
      }
      if (path.endsWith('/tickets/assignment-candidates')) {
        return response([
          {
            user_id: '436df704-2d42-4e09-91cf-d615a748878b',
            display_name: 'Alex Morgan',
          },
          {
            user_id: 'bc67d2f3-aab8-49e4-9588-699edccf86c9',
            display_name: 'Nora Agent',
          },
        ])
      }
      if (path.endsWith(`/tickets/${ticket.id}`)) {
        return response({
          ...ticket,
          status: ticketStatus,
          assigned_agent_id: assignedAgentId,
          version,
          sla_state: 'ON_TRACK',
          first_response_deadline: null,
          resolution_deadline: null,
          updated_at: ticket.created_at,
        })
      }
      if (path.includes(`/tickets/${ticket.id}/comments?`)) {
        return response({ items: comments, next_cursor: null })
      }
      if (path.endsWith(`/tickets/${ticket.id}/comments`) && init?.method === 'POST') {
        const payload = JSON.parse(String(init.body)) as { kind: 'PUBLIC' | 'INTERNAL'; body: string }
        const comment = {
          id: crypto.randomUUID(),
          author_id: '436df704-2d42-4e09-91cf-d615a748878b',
          kind: payload.kind,
          body: payload.body,
          created_at: '2026-07-18T09:05:00Z',
        }
        comments.push(comment)
        return response(comment, 201)
      }
      if (path.endsWith(`/tickets/${ticket.id}/assignment`) && init?.method === 'POST') {
        const payload = JSON.parse(String(init.body)) as { assigned_agent_id: string }
        assignedAgentId = payload.assigned_agent_id
        version += 1
        return response({ ...ticket, assigned_agent_id: assignedAgentId, version })
      }
      if (path.endsWith(`/tickets/${ticket.id}/transitions`) && init?.method === 'POST') {
        const payload = JSON.parse(String(init.body)) as { status: string }
        ticketStatus = payload.status
        version += 1
        return response({ ...ticket, status: ticketStatus, version })
      }
      if (path.includes(`/tickets/${ticket.id}/timeline?`)) {
        return response({
          items: [{
            id: 'b01c99ea-b96b-4c2e-8e9a-92f5fbcde6f1',
            event_type: comments.length > 0 ? 'COMMENT_ADDED' : 'TICKET_CREATED',
            actor_type: 'USER',
            created_at: ticket.created_at,
          }],
          next_cursor: null,
        })
      }
      throw new Error(`Unexpected request: ${path}`)
    })
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()
    renderApp('/login')

    await user.type(screen.getByLabelText('Email address'), 'alex@example.com')
    await user.type(screen.getByLabelText(/^Password/), 'Long secure password 123!')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('heading', { name: 'Agent queue' })).toBeVisible()
    const workspaceNavigation = screen.getByRole('navigation', { name: 'Workspace sections' })
    expect(within(workspaceNavigation).getByRole('button', { name: 'Requests' })).toHaveAttribute('aria-current', 'page')
    await user.click(within(workspaceNavigation).getByRole('button', { name: 'Notifications' }))
    expect(await screen.findByRole('heading', { name: 'Notifications' })).toBeVisible()
    expect(await screen.findByText('Live updates')).toBeVisible()
    expect(screen.getByText('1 unread')).toBeVisible()
    expect(socketConnections).toEqual([{
      url: 'ws://localhost:3000/api/v1/organisations/314bf529-de12-46b6-81e2-770889ff4203/ws',
      protocols: ['bearer', 'access-token'],
    }])
    await user.click(screen.getByRole('button', { name: 'Mark as read' }))
    expect(await screen.findByText('0 unread')).toBeVisible()
    await user.click(within(workspaceNavigation).getByRole('button', { name: 'Requests' }))
    await user.selectOptions(
      screen.getByRole('combobox', { name: /^Category/ }),
      'b2e8a418-8d73-4ce4-8b84-0961e8010e52',
    )
    await user.type(screen.getByLabelText('Title'), ticket.title)
    await user.type(screen.getByLabelText('Description', { selector: 'textarea' }), ticket.description)
    await user.click(screen.getByRole('button', { name: 'Submit request' }))

    expect(await screen.findByRole('heading', { name: ticket.title })).toBeVisible()
    expect(fetchMock.mock.calls.some(([, init]) => new Headers(init?.headers).has('Idempotency-Key'))).toBe(true)

    await user.click(screen.getByRole('button', { name: ticket.title }))
    expect(await screen.findByRole('heading', { name: 'Conversation and internal notes' })).toBeVisible()
    expect(screen.getByRole('heading', { name: 'Timeline' })).toBeVisible()
    expect(screen.getByRole('heading', { name: 'AI suggestions with human review' })).toBeVisible()
    await user.click(screen.getByRole('button', { name: 'Generate suggestions' }))
    const prioritySuggestion = (await screen.findByRole('heading', { name: 'Priority recommendation' })).closest('article')!
    expect(within(prioritySuggestion).getByText('Suggested priority:')).toHaveTextContent('CRITICAL')
    await user.click(within(prioritySuggestion).getByRole('button', { name: 'Accept suggestion' }))
    expect(await within(prioritySuggestion).findByText('accepted')).toBeVisible()
    expect(within(prioritySuggestion).getByText(/Decision recorded only/)).toBeVisible()
    const duplicateSuggestion = screen.getByRole('heading', { name: 'Possible duplicates' }).closest('article')!
    expect(within(duplicateSuggestion).getByText('Below the configured confidence threshold.')).toBeVisible()
    await user.click(within(duplicateSuggestion).getByRole('button', { name: 'Reject suggestion' }))
    expect(await within(duplicateSuggestion).findByText('rejected')).toBeVisible()
    expect(screen.getByText('HIGH', { selector: '.detail-badges span' })).toBeVisible()
    await user.selectOptions(screen.getByLabelText('Assign agent'), 'bc67d2f3-aab8-49e4-9588-699edccf86c9')
    await user.click(screen.getByRole('button', { name: 'Assign selected agent' }))
    expect(await screen.findByText('Nora Agent', { selector: 'dd' })).toBeVisible()
    await user.click(screen.getByRole('button', { name: 'Update status' }))
    expect(await screen.findByText('Triaged', { selector: '.detail-badges span' })).toBeVisible()

    const publicReply = 'Please use the side entrance while the area is inspected.'
    await user.type(screen.getByLabelText('Add a reply'), publicReply)
    await user.click(screen.getByRole('button', { name: 'Post reply' }))
    expect(await screen.findByText(publicReply)).toBeVisible()
    await user.selectOptions(screen.getByLabelText('Reply type'), 'INTERNAL')
    await user.type(screen.getByLabelText('Add a reply'), 'Facilities key is in the secure cabinet.')
    await user.click(screen.getByRole('button', { name: 'Post reply' }))
    expect(await screen.findByText('Facilities key is in the secure cabinet.')).toBeVisible()
    expect(screen.getByText(/You · Internal note/)).toBeVisible()

    await user.click(screen.getByRole('button', { name: /Back to requests/ }))
    await user.type(screen.getByLabelText('Search requests'), 'water leak')
    await user.click(screen.getByRole('button', { name: 'Search' }))
    expect(await screen.findByRole('heading', { name: ticket.title })).toBeVisible()

    await user.click(within(workspaceNavigation).getByRole('button', { name: 'Administration' }))
    expect(await screen.findByRole('heading', { name: 'Administration' })).toBeVisible()
    expect(await screen.findByText('Alex Morgan')).toBeVisible()
    expect(screen.getByText('1 members · 0 invitations')).toBeVisible()
    await user.type(screen.getByLabelText('Email address', { selector: '.administration-workspace input' }), 'agent@example.com')
    await user.selectOptions(screen.getByLabelText('Organisation role'), '06157045-c977-4c99-96cc-f5c05efce053')
    await user.click(screen.getByRole('button', { name: 'Create invitation' }))
    expect(await screen.findByText(/Invitation created for agent@example.com/)).toBeVisible()
    expect(await screen.findByText('1 members · 1 invitations')).toBeVisible()
    const invitationItem = screen.getByText('agent@example.com').closest('li')!
    await user.click(within(invitationItem).getByRole('button', { name: 'Resend invitation for agent@example.com' }))
    expect(await screen.findByText('Invitation token rotated.')).toBeVisible()
    await user.click(within(invitationItem).getByRole('button', { name: 'Revoke invitation for agent@example.com' }))
    expect(await within(invitationItem).findByText('REVOKED')).toBeVisible()

    await user.type(screen.getByLabelText('Calendar name'), 'India weekdays')
    await user.click(screen.getByRole('button', { name: 'Add calendar' }))
    expect(await screen.findByText('1 calendars · 0 policies')).toBeVisible()
    await user.click(screen.getByRole('button', { name: 'Add SLA policy' }))
    expect(await screen.findByText('HIGH · 60/240 minutes')).toBeVisible()
  }, 20_000)
})
