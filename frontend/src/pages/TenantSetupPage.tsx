import { useState, type FormEvent } from 'react'
import { useNavigate, Navigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../auth/useAuth'
import { Brand } from '../components/Brand'

type Organisation = {
  id: string
  name: string
  slug: string
  is_active: boolean
}

export function TenantSetupPage() {
  const { user, request } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
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
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['organisations'] })
      navigate('/dashboard', { replace: true })
    },
    onError: () => setCreateError('That workspace could not be created. Check the name and slug.'),
  })

  // If user already has a workspace, never show setup again
  if (!organisations.isPending && (organisations.data ?? []).length > 0) {
    return <Navigate to="/dashboard" replace />
  }

  function submitOrganisation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setCreateError(null)
    const values = new FormData(event.currentTarget)
    createOrganisation.mutate({
      name: String(values.get('name')),
      slug: String(values.get('slug')),
    })
  }

  if (organisations.isPending) {
    return (
      <main className="centered-page" aria-live="polite">
        <div className="loading-mark" aria-hidden="true" />
        <p>Checking workspace setup…</p>
      </main>
    )
  }

  return (
    <main className="login-layout">
      <section className="login-story">
        <Brand />
        <div className="story-copy">
          <p className="eyebrow">Enterprise Service Management</p>

          <h1>Welcome to ResolveHub.</h1>
          <p>
            Create your organisation workspace to get started with IT service requests, incidents,
            knowledge management, and AI copilot operations.
          </p>
        </div>
        <p className="story-footnote">Secure, tenant-isolated operations for every team.</p>
      </section>

      <section className="login-panel">
        <div className="login-card">
          <div>
            <p className="eyebrow">Initial Workspace Setup</p>
            <h2>Good to see you, {firstName}.</h2>
            <p className="muted">Create your primary tenant workspace to begin using ResolveHub.</p>
          </div>

          <form className="compact-form" onSubmit={submitOrganisation}>
            <label>
              <span>Organisation name</span>
              <input name="name" minLength={2} maxLength={160} placeholder="Acme Operations" required autoFocus />
            </label>
            <label>
              <span>Workspace slug</span>
              <input
                name="slug"
                pattern="[a-z0-9]+(?:-[a-z0-9]+)*"
                minLength={2}
                maxLength={80}
                placeholder="acme-operations"
                required
              />
            </label>

            {createError && <div className="form-error" role="alert">{createError}</div>}

            <button className="primary-button" type="submit" disabled={createOrganisation.isPending}>
              {createOrganisation.isPending ? 'Creating workspace…' : 'Create workspace'}
              {!createOrganisation.isPending && <span aria-hidden="true">→</span>}
            </button>
          </form>
        </div>
      </section>
    </main>
  )
}
