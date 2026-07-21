import { useEffect, useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Brand } from '../components/Brand'
import { useAuth } from '../auth/useAuth'
import { TicketWorkspace } from '../features/tickets/TicketWorkspace'
import { AdministrationWorkspace } from '../features/administration/AdministrationWorkspace'
import { NotificationCenter } from '../features/notifications/NotificationCenter'

type Organisation = {
  id: string
  name: string
  slug: string
  is_active: boolean
}

type MembershipContext = {
  permissions: string[]
}

type WorkspaceView = 'requests' | 'notifications' | 'administration'

export function AppShell() {
  const { user, logout, request } = useAuth()
  const queryClient = useQueryClient()
  const [selectedId, setSelectedId] = useState<string>('')
  const [activeView, setActiveView] = useState<WorkspaceView>('requests')
  const [createError, setCreateError] = useState<string | null>(null)
  const firstName = user?.display_name.split(/\s|@/)[0] || 'there'
  const organisations = useQuery({
    queryKey: ['organisations'],
    queryFn: () => request<Organisation[]>('/organisations'),
  })
  const createOrganisation = useMutation({
    mutationFn: (payload: { name: string; slug: string }) =>
      request<Organisation>('/organisations', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    onSuccess: async (organisation) => {
      setSelectedId(organisation.id)
      await queryClient.invalidateQueries({ queryKey: ['organisations'] })
    },
    onError: () => setCreateError('That workspace could not be created. Check the name and slug.'),
  })
  const items = organisations.data ?? []
  const activeId = selectedId || items[0]?.id || ''
  const activeOrganisation = items.find((item) => item.id === activeId)
  const membership = useQuery({
    queryKey: ['membership', activeId],
    queryFn: () => request<MembershipContext>(`/organisations/${activeId}/membership/me`),
    enabled: Boolean(activeId),
  })
  const permissions = membership.data?.permissions ?? []
  const canReadNotifications = permissions.includes('notification:read')
  const canAdminister = [
    'member:invite',
    'member:read',
    'department:create',
    'category:create',
    'sla:manage',
  ].some((permission) => permissions.includes(permission))

  useEffect(() => setActiveView('requests'), [activeId])

  function submitOrganisation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setCreateError(null)
    const values = new FormData(event.currentTarget)
    createOrganisation.mutate({
      name: String(values.get('name')),
      slug: String(values.get('slug')),
    })
  }

  return (
    <div className="app-frame">
      <header className="app-header">
        <Brand />
        <div className="account-actions">
          <span>{user?.email}</span>
          <button className="quiet-button" type="button" onClick={() => void logout()}>
            Sign out
          </button>
        </div>
      </header>
      <main className="workspace">
        <p className="eyebrow">Your workspace</p>
        <h1>Good to see you, {firstName}.</h1>
        <p className="workspace-lead">
          Choose the organisation you want to work in. ResolveHub will keep every following request
          inside that authorised tenant boundary.
        </p>

        {organisations.isPending && <p className="section-message" role="status">Loading organisations…</p>}
        {organisations.isError && (
          <div className="form-error organisation-state" role="alert">
            Organisations could not be loaded. Sign out and try again.
          </div>
        )}

        {!organisations.isPending && !organisations.isError && items.length === 0 && (
          <section className="organisation-onboarding" aria-labelledby="organisation-title">
            <div>
              <p className="card-label">First setup</p>
              <h2 id="organisation-title">Create your organisation</h2>
              <p>Start a tenant workspace before creating departments, categories, or tickets.</p>
            </div>
            <form className="compact-form" onSubmit={submitOrganisation}>
              <label>
                <span>Organisation name</span>
                <input name="name" minLength={2} maxLength={160} required />
              </label>
              <label>
                <span>Workspace slug</span>
                <input
                  name="slug"
                  pattern="[a-z0-9]+(?:-[a-z0-9]+)*"
                  minLength={2}
                  maxLength={80}
                  placeholder="northstar-operations"
                  required
                />
              </label>
              {createError && <div className="form-error" role="alert">{createError}</div>}
              <button className="primary-button" type="submit" disabled={createOrganisation.isPending}>
                {createOrganisation.isPending ? 'Creating…' : 'Create workspace'}
                {!createOrganisation.isPending && <span aria-hidden="true">→</span>}
              </button>
            </form>
          </section>
        )}

        {items.length > 0 && (
          <>
            <section className="organisation-workspace" aria-labelledby="selected-organisation">
              <label className="organisation-select">
                <span>Organisation</span>
                <select value={activeId} onChange={(event) => setSelectedId(event.target.value)}>
                  {items.map((organisation) => (
                    <option key={organisation.id} value={organisation.id}>{organisation.name}</option>
                  ))}
                </select>
              </label>
              <div className="selected-organisation">
                <p className="card-label">Selected tenant</p>
                <h2 id="selected-organisation">{activeOrganisation?.name}</h2>
                <p>Workspace key: {activeOrganisation?.slug}</p>
              </div>
            </section>
            {!membership.isPending && !membership.isError && (
              <nav className="workspace-navigation" aria-label="Workspace sections">
                <button
                  type="button"
                  aria-current={activeView === 'requests' ? 'page' : undefined}
                  onClick={() => setActiveView('requests')}
                >
                  Requests
                </button>
                {canReadNotifications && (
                  <button
                    type="button"
                    aria-current={activeView === 'notifications' ? 'page' : undefined}
                    onClick={() => setActiveView('notifications')}
                  >
                    Notifications
                  </button>
                )}
                {canAdminister && (
                  <button
                    type="button"
                    aria-current={activeView === 'administration' ? 'page' : undefined}
                    onClick={() => setActiveView('administration')}
                  >
                    Administration
                  </button>
                )}
              </nav>
            )}
            {membership.isError && (
              <div className="form-error organisation-state" role="alert">
                Your workspace permissions could not be loaded.
              </div>
            )}
            {activeOrganisation && (
              <div hidden={activeView !== 'requests'}>
                <TicketWorkspace organisationId={activeOrganisation.id} />
              </div>
            )}
            {activeOrganisation && canReadNotifications && (
              <div hidden={activeView !== 'notifications'}>
                <NotificationCenter organisationId={activeOrganisation.id} />
              </div>
            )}
            {activeOrganisation && canAdminister && (
              <div hidden={activeView !== 'administration'}>
                <AdministrationWorkspace organisationId={activeOrganisation.id} />
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}
