import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../auth/useAuth'

type Organisation = {
  id: string
  name: string
  slug: string
  is_active: boolean
}

export function useActiveOrganisation() {
  const { request } = useAuth()

  const query = useQuery({
    queryKey: ['organisations'],
    queryFn: () => request<Organisation[]>('/organisations'),
  })

  const organisations = query.data ?? []
  const savedOrgId = typeof window !== 'undefined' ? localStorage.getItem('resolvehub_active_org_id') : null
  const activeOrganisation = (savedOrgId ? organisations.find((o) => o.id === savedOrgId) : null) ?? organisations[0] ?? null
  const organisationId = activeOrganisation?.id ?? ''

  return {
    organisationId,
    activeOrganisation,
    organisations,
    isLoading: query.isPending && organisations.length === 0,
    isError: query.isError,
  }
}
