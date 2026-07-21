import { expect, test } from '@playwright/test'

test.skip(!process.env.LIVE_API, 'Set LIVE_API=true to run against the local ResolveHub API')
test.setTimeout(240_000)

test('new requester reaches a tenant-scoped submitted ticket', async ({ page }) => {
  const email = `playwright-${crypto.randomUUID()}@example.com`
  const agentEmail = `agent-${crypto.randomUUID()}@example.com`
  const revokedEmail = `revoked-${crypto.randomUUID()}@example.com`
  const password = 'Long secure password 123!'

  await expect
    .poll(async () => {
      const response = await page.request.get('http://127.0.0.1:8000/health/ready')
      return response.ok()
    }, { timeout: 60_000, message: 'ResolveHub API did not become ready' })
    .toBe(true)

  await page.goto('/register')
  await page.getByLabel('Full name').fill('Playwright Operator')
  await page.getByLabel('Email address').fill(email)
  await page.getByLabel(/^Password/).fill(password)
  await page.getByLabel('Confirm password').fill(password)
  await page.getByRole('button', { name: 'Create account' }).click()

  await expect(page.getByRole('heading', { name: 'Verify your email' })).toBeVisible({
    timeout: 60_000,
  })
  await expect(page.getByLabel('Verification token')).not.toHaveValue('')
  await page.getByRole('button', { name: 'Verify account' }).click()

  await expect(page.getByRole('status')).toContainText('Email verified')
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: 'Sign in' }).click()

  await expect(
    page.getByRole('heading', { name: 'Good to see you, Playwright.' }),
  ).toBeVisible({ timeout: 60_000 })
  await page.getByLabel('Organisation name').fill('Playwright Services')
  await page.getByLabel('Workspace slug').fill(`playwright-${crypto.randomUUID()}`)
  await page.getByRole('button', { name: 'Create workspace' }).click()
  await expect(page.getByRole('heading', { name: 'Playwright Services' })).toBeVisible({
    timeout: 60_000,
  })

  await expect(page.getByRole('heading', { name: 'Configure the first service' })).toBeVisible({
    timeout: 60_000,
  })
  await page.getByLabel('Department name').fill('Facilities')
  await page.getByLabel('Service category').fill('Building maintenance')
  await page.getByLabel('Default priority').selectOption('HIGH')
  await page.getByRole('button', { name: 'Configure service' }).click()

  await expect(page.getByRole('heading', { name: 'Agent queue' })).toBeVisible({
    timeout: 60_000,
  })
  const workspaceNavigation = page.getByRole('navigation', { name: 'Workspace sections' })
  await expect(workspaceNavigation.getByRole('button', { name: 'Requests' })).toHaveAttribute(
    'aria-current',
    'page',
  )
  await workspaceNavigation.getByRole('button', { name: 'Notifications' }).click()
  await expect(page.getByRole('heading', { name: 'Notifications' })).toBeVisible({
    timeout: 60_000,
  })
  await expect(page.getByText('Live updates')).toBeVisible({ timeout: 60_000 })
  await workspaceNavigation.getByRole('button', { name: 'Administration' }).click()
  await expect(page.getByRole('heading', { name: 'Administration' })).toBeVisible({
    timeout: 60_000,
  })
  await expect(page.getByText('Playwright Operator')).toBeVisible({ timeout: 60_000 })
  await expect(page.getByText('1 members · 0 invitations')).toBeVisible({ timeout: 60_000 })

  await page.getByLabel('Email address', { exact: true }).last().fill(agentEmail)
  await page.getByLabel('Organisation role').selectOption({ label: 'Agent' })
  await page.getByRole('button', { name: 'Create invitation' }).click()
  await expect(page.getByText(/Invitation created for agent-/)).toBeVisible({ timeout: 60_000 })
  await expect(page.getByText('1 members · 1 invitations')).toBeVisible({ timeout: 60_000 })
  await page.getByRole('button', { name: `Resend invitation for ${agentEmail}` }).click()
  const rotatedInvitation = page.getByRole('status').filter({
    hasText: 'Invitation token rotated.',
  })
  await expect(rotatedInvitation).toBeVisible({ timeout: 60_000 })
  const invitationToken = await rotatedInvitation.locator('code').textContent()
  expect(invitationToken).toBeTruthy()
  const agentRegistration = await page.request.post('http://127.0.0.1:8000/api/v1/auth/register', {
    data: { email: agentEmail, password, display_name: 'Browser Agent' },
  })
  expect(agentRegistration.status()).toBe(202)
  const agentVerificationToken = (await agentRegistration.json()).verification_token as string
  expect(agentVerificationToken).toBeTruthy()
  const agentVerification = await page.request.post(
    'http://127.0.0.1:8000/api/v1/auth/verify-email',
    { data: { token: agentVerificationToken } },
  )
  expect(agentVerification.status()).toBe(204)
  const agentLogin = await page.request.post('http://127.0.0.1:8000/api/v1/auth/login', {
    data: { email: agentEmail, password },
  })
  expect(agentLogin.ok()).toBeTruthy()
  const agentAccessToken = (await agentLogin.json()).access_token as string
  const invitationAcceptance = await page.request.post(
    'http://127.0.0.1:8000/api/v1/invitations/accept',
    {
      headers: { Authorization: `Bearer ${agentAccessToken}` },
      data: { token: invitationToken },
    },
  )
  expect(invitationAcceptance.ok()).toBeTruthy()

  await page.getByLabel('Email address', { exact: true }).last().fill(revokedEmail)
  await page.getByLabel('Organisation role').selectOption({ label: 'Agent' })
  await page.getByRole('button', { name: 'Create invitation' }).click()
  await expect(page.getByText(`Invitation created for ${revokedEmail}.`, { exact: false })).toBeVisible({
    timeout: 60_000,
  })
  await page.getByRole('button', { name: `Revoke invitation for ${revokedEmail}` }).click()
  const revokedInvitation = page.locator('.invitation-history li').filter({ hasText: revokedEmail })
  await expect(revokedInvitation.getByText('REVOKED')).toBeVisible({ timeout: 60_000 })

  await page.getByLabel('New department name').fill('Customer support')
  await page.getByRole('button', { name: 'Add department' }).click()
  await expect(page.getByText('2 departments · 1 categories')).toBeVisible({ timeout: 60_000 })
  await page.locator('select[name="department_id"]').selectOption({ label: 'Customer support' })
  await page.getByLabel('Category name').fill('Access requests')
  await page.getByRole('button', { name: 'Add category' }).click()
  await expect(page.getByText('2 departments · 2 categories')).toBeVisible({ timeout: 60_000 })

  await page.getByLabel('Calendar name').fill('India weekdays')
  await page.getByRole('button', { name: 'Add calendar' }).click()
  await expect(page.getByText('1 calendars · 0 policies')).toBeVisible({ timeout: 60_000 })
  await page.getByLabel('Holiday date').fill('2030-01-15')
  await page.getByLabel('Holiday name').fill('Operations planning day')
  await page.getByRole('button', { name: 'Add holiday' }).click()
  await expect(page.getByText('Holiday added.')).toBeVisible({ timeout: 60_000 })
  await page.getByLabel('Policy category').selectOption({ label: 'Building maintenance' })
  await page.getByRole('button', { name: 'Add SLA policy' }).click()
  await expect(page.getByText('1 calendars · 1 policies')).toBeVisible({ timeout: 60_000 })

  await workspaceNavigation.getByRole('button', { name: 'Requests' }).click()
  await page.locator('select[name="category_id"]').selectOption({
    label: 'Building maintenance',
  })
  await page.getByLabel('Title').fill('Water leak near reception')
  await page
    .getByLabel('Description', { exact: true })
    .fill('Water is leaking continuously from the pipe beside the reception entrance.')
  await page.getByRole('button', { name: 'Submit request' }).click()
  await expect(page.getByRole('heading', { name: 'Water leak near reception' })).toBeVisible({
    timeout: 60_000,
  })
  await workspaceNavigation.getByRole('button', { name: 'Notifications' }).click()
  await expect(page.getByText('Ticket created', { exact: true }).last()).toBeVisible({
    timeout: 60_000,
  })
  await expect(page.getByText(/unread$/)).not.toHaveText('0 unread')
  await page.getByRole('button', { name: 'Mark as read' }).last().click()

  await workspaceNavigation.getByRole('button', { name: 'Requests' }).click()
  await page.getByRole('button', { name: 'Water leak near reception' }).click()
  await expect(page.getByRole('heading', { name: 'Conversation and internal notes' })).toBeVisible({
    timeout: 60_000,
  })
  await expect(page.getByRole('heading', { name: 'Timeline' })).toBeVisible()
  await expect(page.locator('.ticket-facts dd').filter({ hasText: 'Active' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'AI suggestions with human review' })).toBeVisible()
  await page.getByRole('button', { name: 'Generate suggestions' }).click()
  const prioritySuggestion = page.locator('.ai-suggestion').filter({
    has: page.getByRole('heading', { name: 'Priority recommendation' }),
  })
  await expect(prioritySuggestion.getByText(/Suggested priority:/)).toContainText('HIGH', {
    timeout: 60_000,
  })
  await prioritySuggestion.getByRole('button', { name: 'Accept suggestion' }).click()
  await expect(prioritySuggestion.getByText('accepted')).toBeVisible({ timeout: 60_000 })
  await expect(prioritySuggestion.getByText(/Decision recorded only/)).toBeVisible()
  const duplicateSuggestion = page.locator('.ai-suggestion').filter({
    has: page.getByRole('heading', { name: 'Possible duplicates' }),
  })
  await expect(duplicateSuggestion.getByText('Below the configured confidence threshold.')).toBeVisible()
  await duplicateSuggestion.getByRole('button', { name: 'Reject suggestion' }).click()
  await expect(duplicateSuggestion.getByText('rejected')).toBeVisible({ timeout: 60_000 })
  await expect(page.locator('.detail-badges').getByText('HIGH')).toBeVisible()
  await page.getByLabel('Assign agent').selectOption({ label: 'Browser Agent' })
  await page.getByRole('button', { name: 'Assign selected agent' }).click()
  await expect(page.locator('.ticket-facts dd').filter({ hasText: 'Browser Agent' })).toBeVisible({
    timeout: 60_000,
  })
  await page.getByRole('button', { name: 'Update status' }).click()
  await expect(page.locator('.detail-badges').getByText('Triaged')).toBeVisible({
    timeout: 60_000,
  })
  await page.getByLabel('Next status').selectOption('ASSIGNED')
  await page.getByRole('button', { name: 'Update status' }).click()
  await expect(page.locator('.detail-badges').getByText('Assigned')).toBeVisible({
    timeout: 60_000,
  })
  await page.getByLabel('Next status').selectOption('IN_PROGRESS')
  await page.getByRole('button', { name: 'Update status' }).click()
  await expect(page.locator('.detail-badges').getByText('In progress')).toBeVisible({
    timeout: 60_000,
  })
  await page.getByLabel('Reply type').selectOption('INTERNAL')
  await page.getByLabel('Add a reply').fill('Facilities key is in the secure cabinet.')
  await page.getByRole('button', { name: 'Post reply' }).click()
  await expect(page.getByText('Facilities key is in the secure cabinet.')).toBeVisible({
    timeout: 60_000,
  })
  await expect(page.getByText(/Internal note/).last()).toBeVisible()
  await page.getByLabel('Reply type').selectOption('PUBLIC')
  await page
    .getByLabel('Add a reply')
    .fill('Please use the side entrance while the area is inspected.')
  await page.getByRole('button', { name: 'Post reply' }).click()
  await expect(
    page.getByText('Please use the side entrance while the area is inspected.'),
  ).toBeVisible({ timeout: 60_000 })

  await page.getByRole('button', { name: /Back to requests/ }).click()
  await page.getByLabel('Search requests').fill('water leak')
  await page.getByRole('button', { name: 'Search' }).click()
  await expect(page.getByRole('heading', { name: 'Water leak near reception' })).toBeVisible({
    timeout: 60_000,
  })
  await page.getByRole('button', { name: 'Sign out' }).click()
  await expect(page.getByRole('heading', { name: 'Sign in to your workspace' })).toBeVisible()
})
