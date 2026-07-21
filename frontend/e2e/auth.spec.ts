import { expect, test } from '@playwright/test'

test('verified user signs in and reaches the secure workspace', async ({ page }) => {
  await page.route('**/api/v1/auth/browser/login', async (route) => {
    expect(route.request().headers()['x-resolvehub-client']).toBe('browser')
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: 'browser-access-token',
        csrf_token: 'browser-csrf-token',
        token_type: 'bearer',
        expires_in: 900,
      }),
    })
  })
  await page.route('**/api/v1/auth/me', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: '436df704-2d42-4e09-91cf-d615a748878b',
        email: 'alex@example.com',
        display_name: 'Alex Morgan',
        is_email_verified: true,
        is_active: true,
      }),
    }),
  )
  await page.route('**/api/v1/organisations', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }),
  )

  await page.goto('/login')
  await page.getByLabel('Email address').fill('alex@example.com')
  await page.getByLabel('Password').fill('Long secure password 123!')
  await page.getByRole('button', { name: 'Sign in' }).click()

  await expect(page.getByRole('heading', { name: 'Good to see you, Alex.' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Create your organisation' })).toBeVisible()
})
