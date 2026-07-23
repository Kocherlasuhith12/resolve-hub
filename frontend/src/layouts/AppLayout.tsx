import { Outlet, Navigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../auth/useAuth'
import { AppShell } from '../pages/AppShell'

type Organisation = {
  id: string
  name: string
  slug: string
  is_active: boolean
}

export function AppLayout() {
  const { request } = useAuth()

  const organisations = useQuery({
    queryKey: ['organisations'],
    queryFn: () => request<Organisation[]>('/organisations'),
  })

  if (organisations.isPending) {
    return (
      <main className="centered-page" aria-live="polite">
        <div className="loading-mark" aria-hidden="true" />
        <p>Loading workspace…</p>
      </main>
    )
  }

  // If user has no workspace, redirect to initial setup
  if ((organisations.data ?? []).length === 0) {
    return <Navigate to="/setup-workspace" replace />
  }

  return (
    <AppShell>
      <Outlet />
    </AppShell>
  )
}
