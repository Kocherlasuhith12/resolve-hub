import { type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../../auth/useAuth'

type Membership = { role_name: string; permissions: string[] }
type Role = { id: string; name: string; permissions: string[] }
type Department = { id: string; name: string; description: string | null; is_active: boolean }
type Category = {
  id: string
  department_id: string
  name: string
  default_priority: string
  is_active: boolean
}
type Calendar = {
  id: string
  name: string
  timezone: string
  weekly_hours: Record<string, string[][]>
  is_active: boolean
}
type Policy = {
  id: string
  category_id: string
  calendar_id: string
  priority: string
  first_response_minutes: number
  resolution_minutes: number
  warning_percent: number
  pause_on_waiting: boolean
  is_active: boolean
}
type Invitation = {
  id: string
  email: string
  expires_at: string
  invitation_token: string | null
}
type InvitationLifecycle = Invitation & {
  role_id: string
  status: 'PENDING' | 'ACCEPTED' | 'REVOKED' | 'EXPIRED'
  accepted_at: string | null
  revoked_at: string | null
  created_at: string
}
type Member = {
  id: string
  user_id: string
  display_name: string
  email: string
  role_id: string
  role_name: string
  is_active: boolean
  created_at: string
}

const priorities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

export function AdministrationWorkspace({ organisationId }: { organisationId: string }) {
  const { request } = useAuth()
  const queryClient = useQueryClient()
  const membership = useQuery({
    queryKey: ['membership', organisationId],
    queryFn: () => request<Membership>(`/organisations/${organisationId}/membership/me`),
  })
  const permissions = new Set(membership.data?.permissions ?? [])
  const canInvite = permissions.has('member:invite') && permissions.has('member:read')
  const canCreateDepartment = permissions.has('department:create')
  const canCreateCategory = permissions.has('category:create')
  const canManageSla = permissions.has('sla:manage')
  const isAdministrator = canInvite || canCreateDepartment || canCreateCategory || canManageSla

  const roles = useQuery({
    queryKey: ['roles', organisationId],
    queryFn: () => request<Role[]>(`/organisations/${organisationId}/roles`),
    enabled: canInvite,
  })
  const members = useQuery({
    queryKey: ['members', organisationId],
    queryFn: () => request<Member[]>(`/organisations/${organisationId}/members`),
    enabled: canInvite,
  })
  const invitations = useQuery({
    queryKey: ['invitations', organisationId],
    queryFn: () =>
      request<InvitationLifecycle[]>(`/organisations/${organisationId}/invitations`),
    enabled: canInvite,
  })
  const departments = useQuery({
    queryKey: ['departments', organisationId],
    queryFn: () => request<Department[]>(`/organisations/${organisationId}/departments`),
    enabled: isAdministrator,
  })
  const categories = useQuery({
    queryKey: ['categories', organisationId],
    queryFn: () => request<Category[]>(`/organisations/${organisationId}/categories`),
    enabled: isAdministrator,
  })
  const calendars = useQuery({
    queryKey: ['sla-calendars', organisationId],
    queryFn: () => request<Calendar[]>(`/organisations/${organisationId}/sla/calendars`),
    enabled: canManageSla,
  })
  const policies = useQuery({
    queryKey: ['sla-policies', organisationId],
    queryFn: () => request<Policy[]>(`/organisations/${organisationId}/sla/policies`),
    enabled: canManageSla,
  })

  const invite = useMutation({
    mutationFn: (payload: { email: string; role_id: string }) =>
      request<Invitation>(`/organisations/${organisationId}/invitations`, {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['invitations', organisationId] })
    },
  })
  const resendInvitation = useMutation({
    mutationFn: (invitationId: string) =>
      request<InvitationLifecycle>(
        `/organisations/${organisationId}/invitations/${invitationId}/resend`,
        { method: 'POST' },
      ),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['invitations', organisationId] })
    },
  })
  const revokeInvitation = useMutation({
    mutationFn: (invitationId: string) =>
      request<InvitationLifecycle>(
        `/organisations/${organisationId}/invitations/${invitationId}/revoke`,
        { method: 'POST' },
      ),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['invitations', organisationId] })
    },
  })
  const createDepartment = useMutation({
    mutationFn: (payload: { name: string; description?: string }) =>
      request<Department>(`/organisations/${organisationId}/departments`, {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['departments', organisationId] })
    },
  })
  const createCategory = useMutation({
    mutationFn: (payload: { department_id: string; name: string; default_priority: string }) =>
      request<Category>(`/organisations/${organisationId}/categories`, {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['categories', organisationId] })
    },
  })
  const createCalendar = useMutation({
    mutationFn: (payload: {
      name: string
      timezone: string
      weekly_hours: Record<string, string[][]>
    }) =>
      request<Calendar>(`/organisations/${organisationId}/sla/calendars`, {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['sla-calendars', organisationId] })
    },
  })
  const addHoliday = useMutation({
    mutationFn: (payload: { calendar_id: string; holiday_date: string; name: string }) =>
      request<void>(`/organisations/${organisationId}/sla/calendars/${payload.calendar_id}/holidays`, {
        method: 'POST',
        body: JSON.stringify({ holiday_date: payload.holiday_date, name: payload.name }),
      }),
  })
  const createPolicy = useMutation({
    mutationFn: (payload: {
      category_id: string
      calendar_id: string
      priority: string
      first_response_minutes: number
      resolution_minutes: number
      warning_percent: number
      pause_on_waiting: boolean
    }) =>
      request<Policy>(`/organisations/${organisationId}/sla/policies`, {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['sla-policies', organisationId] })
    },
  })

  if (membership.isPending) return <p className="section-message">Loading administration…</p>
  if (membership.isError || !isAdministrator) return null
  if (categories.isPending || (categories.data?.length ?? 0) === 0) return null

  function values(event: FormEvent<HTMLFormElement>): FormData {
    event.preventDefault()
    return new FormData(event.currentTarget)
  }

  return (
    <section className="administration-workspace" aria-labelledby="administration-title">
      <header className="admin-header">
        <div>
          <p className="card-label">Permission-backed controls</p>
          <h2 id="administration-title">Administration</h2>
        </div>
        <span>{membership.data.role_name}</span>
      </header>

      {canInvite && (
        <section className="admin-panel" aria-labelledby="people-title">
          <div>
            <h3 id="people-title">People and invitations</h3>
            <p>{members.data?.length ?? 0} members · {invitations.data?.length ?? 0} invitations</p>
            <ul className="admin-list people-list">
              {(members.data ?? []).map((member) => (
                <li key={member.id}>
                  <span><strong>{member.display_name}</strong><small>{member.email}</small></span>
                  <span>{member.role_name}{member.is_active ? '' : ' · Inactive'}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="admin-form-stack">
            <form className="compact-form" onSubmit={(event) => {
              const data = values(event)
              invite.mutate({ email: String(data.get('email')), role_id: String(data.get('role_id')) })
            }}>
              <h4>Invite a team member</h4>
              <label><span>Email address</span><input name="email" type="email" required /></label>
              <label><span>Organisation role</span><select name="role_id" required defaultValue="">
                <option value="" disabled>Select a role</option>
                {(roles.data ?? []).map((role) => <option key={role.id} value={role.id}>{role.name}</option>)}
              </select></label>
              <button className="primary-button" type="submit" disabled={invite.isPending || roles.isPending}>{invite.isPending ? 'Inviting…' : 'Create invitation'}</button>
              {invite.isError && <div className="form-error" role="alert">The invitation could not be created.</div>}
              {invite.data && <div className="form-success" role="status">
                Invitation created for {invite.data.email}.
                {invite.data.invitation_token && <small> Local acceptance token: <code>{invite.data.invitation_token}</code></small>}
              </div>}
            </form>
            <div className="invitation-history">
              <h4>Invitation history</h4>
              {(members.isError || invitations.isError) && <div className="form-error" role="alert">People could not be loaded.</div>}
              <ul className="admin-list">
                {(invitations.data ?? []).map((invitation) => (
                  <li key={invitation.id}>
                    <span><strong>{invitation.email}</strong><small>{roles.data?.find((role) => role.id === invitation.role_id)?.name ?? 'Role'}</small></span>
                    <span className="invitation-actions">
                      <strong>{invitation.status}</strong>
                      {invitation.status === 'PENDING' && <>
                        <button className="text-button" type="button" aria-label={`Resend invitation for ${invitation.email}`} disabled={resendInvitation.isPending} onClick={() => resendInvitation.mutate(invitation.id)}>Resend</button>
                        <button className="text-button danger-text" type="button" aria-label={`Revoke invitation for ${invitation.email}`} disabled={revokeInvitation.isPending} onClick={() => revokeInvitation.mutate(invitation.id)}>Revoke</button>
                      </>}
                    </span>
                  </li>
                ))}
              </ul>
              {(resendInvitation.isError || revokeInvitation.isError) && <div className="form-error" role="alert">The invitation lifecycle change could not be saved.</div>}
              {resendInvitation.data?.invitation_token && <div className="form-success" role="status">Invitation token rotated.<small> Local acceptance token: <code>{resendInvitation.data.invitation_token}</code></small></div>}
            </div>
          </div>
        </section>
      )}

      <section className="admin-panel" aria-labelledby="catalogue-title">
        <div>
          <h3 id="catalogue-title">Service catalogue</h3>
          <p>{departments.data?.length ?? 0} departments · {categories.data?.length ?? 0} categories</p>
          <ul className="admin-list">{(categories.data ?? []).map((category) => <li key={category.id}>{category.name}<span>{category.default_priority}</span></li>)}</ul>
        </div>
        <div className="admin-form-stack">
          {canCreateDepartment && <form className="compact-form" onSubmit={(event) => {
            const data = values(event)
            const description = String(data.get('description') || '').trim()
            createDepartment.mutate({ name: String(data.get('department_name')), ...(description ? { description } : {}) })
          }}>
            <h4>Add department</h4>
            <label><span>New department name</span><input name="department_name" minLength={2} maxLength={120} required /></label>
            <label><span>Department description</span><input name="description" maxLength={500} /></label>
            <button className="quiet-button" type="submit" disabled={createDepartment.isPending}>Add department</button>
          </form>}
          {canCreateCategory && <form className="compact-form" onSubmit={(event) => {
            const data = values(event)
            createCategory.mutate({
              department_id: String(data.get('department_id')),
              name: String(data.get('category_name')),
              default_priority: String(data.get('default_priority')),
            })
          }}>
            <h4>Add service category</h4>
            <label><span>Department</span><select name="department_id" required defaultValue="">
              <option value="" disabled>Select a department</option>
              {(departments.data ?? []).map((department) => <option key={department.id} value={department.id}>{department.name}</option>)}
            </select></label>
            <label><span>Category name</span><input name="category_name" minLength={2} maxLength={120} required /></label>
            <label><span>Default priority</span><select name="default_priority" defaultValue="MEDIUM">{priorities.map((priority) => <option key={priority}>{priority}</option>)}</select></label>
            <button className="quiet-button" type="submit" disabled={createCategory.isPending}>Add category</button>
          </form>}
          {(createDepartment.isError || createCategory.isError) && <div className="form-error" role="alert">The catalogue change could not be saved.</div>}
        </div>
      </section>

      {canManageSla && (
        <section className="admin-panel sla-admin" aria-labelledby="sla-admin-title">
          <div>
            <h3 id="sla-admin-title">Business hours and SLA</h3>
            <p>{calendars.data?.length ?? 0} calendars · {policies.data?.length ?? 0} policies</p>
            <ul className="admin-list">{(policies.data ?? []).map((policy) => <li key={policy.id}>{policy.priority} · {policy.first_response_minutes}/{policy.resolution_minutes} minutes</li>)}</ul>
          </div>
          <div className="admin-form-stack">
            <form className="compact-form" onSubmit={(event) => {
              const data = values(event)
              const interval = [[String(data.get('opens_at')), String(data.get('closes_at'))]]
              createCalendar.mutate({
                name: String(data.get('calendar_name')),
                timezone: String(data.get('timezone')),
                weekly_hours: { '0': interval, '1': interval, '2': interval, '3': interval, '4': interval },
              })
            }}>
              <h4>Add weekday calendar</h4>
              <label><span>Calendar name</span><input name="calendar_name" minLength={2} maxLength={120} required /></label>
              <label><span>IANA timezone</span><input name="timezone" defaultValue="Asia/Kolkata" required /></label>
              <div className="inline-fields"><label><span>Opens</span><input name="opens_at" type="time" defaultValue="09:00" required /></label><label><span>Closes</span><input name="closes_at" type="time" defaultValue="17:00" required /></label></div>
              <button className="quiet-button" type="submit" disabled={createCalendar.isPending}>Add calendar</button>
            </form>
            {(calendars.data ?? []).length > 0 && <form className="compact-form" onSubmit={(event) => {
              const data = values(event)
              addHoliday.mutate({ calendar_id: String(data.get('holiday_calendar_id')), holiday_date: String(data.get('holiday_date')), name: String(data.get('holiday_name')) })
            }}>
              <h4>Add holiday</h4>
              <label><span>Calendar</span><select name="holiday_calendar_id" required>{(calendars.data ?? []).map((calendar) => <option key={calendar.id} value={calendar.id}>{calendar.name}</option>)}</select></label>
              <label><span>Holiday date</span><input name="holiday_date" type="date" required /></label>
              <label><span>Holiday name</span><input name="holiday_name" minLength={2} maxLength={120} required /></label>
              <button className="quiet-button" type="submit" disabled={addHoliday.isPending}>Add holiday</button>
              {addHoliday.isSuccess && <div className="form-success" role="status">Holiday added.</div>}
            </form>}
            {(calendars.data ?? []).length > 0 && (categories.data ?? []).length > 0 && <form className="compact-form" onSubmit={(event) => {
              const data = values(event)
              createPolicy.mutate({
                category_id: String(data.get('policy_category_id')),
                calendar_id: String(data.get('policy_calendar_id')),
                priority: String(data.get('policy_priority')),
                first_response_minutes: Number(data.get('first_response_minutes')),
                resolution_minutes: Number(data.get('resolution_minutes')),
                warning_percent: Number(data.get('warning_percent')),
                pause_on_waiting: Boolean(data.get('pause_on_waiting')),
              })
            }}>
              <h4>Add SLA policy</h4>
              <label><span>Policy category</span><select name="policy_category_id" required>{(categories.data ?? []).map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</select></label>
              <label><span>Policy calendar</span><select name="policy_calendar_id" required>{(calendars.data ?? []).map((calendar) => <option key={calendar.id} value={calendar.id}>{calendar.name}</option>)}</select></label>
              <label><span>Policy priority</span><select name="policy_priority" defaultValue="HIGH">{priorities.map((priority) => <option key={priority}>{priority}</option>)}</select></label>
              <div className="inline-fields"><label><span>First response minutes</span><input name="first_response_minutes" type="number" min={1} defaultValue={60} required /></label><label><span>Resolution minutes</span><input name="resolution_minutes" type="number" min={1} defaultValue={240} required /></label></div>
              <label><span>Warning percent</span><input name="warning_percent" type="number" min={1} max={99} defaultValue={80} required /></label>
              <label className="checkbox-label"><input name="pause_on_waiting" type="checkbox" defaultChecked /><span>Pause while waiting for requester</span></label>
              <button className="primary-button" type="submit" disabled={createPolicy.isPending}>Add SLA policy</button>
            </form>}
            {(createCalendar.isError || addHoliday.isError || createPolicy.isError) && <div className="form-error" role="alert">The SLA configuration could not be saved.</div>}
          </div>
        </section>
      )}
    </section>
  )
}
