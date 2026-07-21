import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { apiRequest, ApiError, type RegisterResponse } from '../api/client'
import { useAuth } from '../auth/useAuth'
import { AuthLayout } from '../components/AuthLayout'
import { AuthTabs } from '../components/AuthTabs'

export function RegisterPage() {
  const { status } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (status === 'authenticated') return <Navigate to="/" replace />

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    const values = new FormData(event.currentTarget)
    const password = String(values.get('password'))
    if (password !== String(values.get('confirm_password'))) {
      setError('Passwords do not match.')
      return
    }
    setSubmitting(true)
    try {
      const email = String(values.get('email'))
      const result = await apiRequest<RegisterResponse>('/auth/register', {
        method: 'POST',
        body: JSON.stringify({
          display_name: String(values.get('display_name')),
          email,
          password,
        }),
      })
      navigate('/verify-email', {
        replace: true,
        state: {
          email,
          message: result.message,
          verificationToken: result.verification_token,
        },
      })
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
          <p className="eyebrow">Start with ResolveHub</p>
          <h2>Create your account</h2>
          <p className="muted">Use an email address you can verify.</p>
        </div>

        <div className="fields">
          <label>
            <span>Full name</span>
            <input name="display_name" autoComplete="name" maxLength={120} required autoFocus />
          </label>
          <label>
            <span>Email address</span>
            <input
              name="email"
              type="email"
              autoComplete="email"
              placeholder="you@company.com"
              required
            />
          </label>
          <label>
            <span>Password</span>
            <input
              name="password"
              type="password"
              autoComplete="new-password"
              minLength={12}
              maxLength={128}
              aria-describedby="password-help"
              required
            />
            <small id="password-help">Use at least 12 characters.</small>
          </label>
          <label>
            <span>Confirm password</span>
            <input
              name="confirm_password"
              type="password"
              autoComplete="new-password"
              minLength={12}
              maxLength={128}
              required
            />
          </label>
        </div>

        {error && <div className="form-error" role="alert">{error}</div>}

        <button className="primary-button" type="submit" disabled={submitting}>
          {submitting ? 'Creating account…' : 'Create account'}
          {!submitting && <span aria-hidden="true">→</span>}
        </button>
        <p className="security-note">
          Login remains locked until the email address has been verified.
        </p>
      </form>
    </AuthLayout>
  )
}
