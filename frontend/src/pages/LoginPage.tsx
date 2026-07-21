import { useState, type FormEvent } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { ApiError } from '../api/client'
import { useAuth } from '../auth/useAuth'
import { AuthLayout } from '../components/AuthLayout'
import { AuthTabs } from '../components/AuthTabs'

type LoginLocationState = { email?: string; verified?: boolean }

export function LoginPage() {
  const { status, login } = useAuth()
  const location = useLocation()
  const locationState = location.state as LoginLocationState | null
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (status === 'authenticated') return <Navigate to="/" replace />

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    const values = new FormData(event.currentTarget)
    try {
      await login(String(values.get('email')), String(values.get('password')))
    } catch (reason) {
      setError(
        reason instanceof ApiError
          ? reason.message
          : 'We could not reach ResolveHub. Check the API and try again.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout>
        <form className="login-card" onSubmit={submit}>
          <AuthTabs />
          <div>
            <p className="eyebrow">Welcome back</p>
            <h2 id="login-title">Sign in to your workspace</h2>
            <p className="muted">Use your verified ResolveHub account.</p>
          </div>

          {locationState?.verified && (
            <div className="form-success" role="status">
              Email verified. You can sign in now.
            </div>
          )}

          <div className="fields">
            <label>
              <span>Email address</span>
              <input
                name="email"
                type="email"
                autoComplete="email"
                placeholder="you@company.com"
                defaultValue={locationState?.email ?? ''}
                required
                autoFocus
              />
            </label>
            <label>
              <span>Password</span>
              <input
                name="password"
                type="password"
                autoComplete="current-password"
                minLength={12}
                required
              />
            </label>
          </div>

          {error && <div className="form-error" role="alert">{error}</div>}

          <button className="primary-button" type="submit" disabled={submitting}>
            {submitting ? 'Signing in…' : 'Sign in'}
            {!submitting && <span aria-hidden="true">→</span>}
          </button>

          <p className="security-note">
            Your session is protected with rotating credentials and automatic expiry.
          </p>
        </form>
    </AuthLayout>
  )
}
