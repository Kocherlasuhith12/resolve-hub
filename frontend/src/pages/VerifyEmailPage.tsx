import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { apiRequest, ApiError } from '../api/client'
import { AuthLayout } from '../components/AuthLayout'

type VerificationLocationState = {
  email?: string
  message?: string
  verificationToken?: string | null
}

export function VerifyEmailPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as VerificationLocationState | null
  const [token, setToken] = useState(state?.verificationToken ?? '')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      await apiRequest<void>('/auth/verify-email', {
        method: 'POST',
        body: JSON.stringify({ token }),
      })
      navigate('/login', {
        replace: true,
        state: { email: state?.email, verified: true },
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
        <div>
          <p className="eyebrow">One more step</p>
          <h2>Verify your email</h2>
          <p className="muted">
            {state?.email ? `We prepared verification for ${state.email}.` : 'Enter the verification token sent for your account.'}
          </p>
        </div>

        <div className="verification-callout">
          <strong>Check your email</strong>
          <span>{state?.message ?? 'Use the verification instructions associated with your registration.'}</span>
          {state?.verificationToken && (
            <small>Local development token loaded securely from the registration response.</small>
          )}
        </div>

        <div className="fields">
          <label>
            <span>Verification token</span>
            <input
              name="token"
              value={token}
              onChange={(event) => setToken(event.target.value)}
              autoComplete="off"
              minLength={32}
              maxLength={256}
              required
              autoFocus={!token}
            />
          </label>
        </div>

        {error && <div className="form-error" role="alert">{error}</div>}

        <button className="primary-button" type="submit" disabled={submitting}>
          {submitting ? 'Verifying…' : 'Verify account'}
          {!submitting && <span aria-hidden="true">→</span>}
        </button>
        <Link className="text-link centered-link" to="/login">Back to sign in</Link>
      </form>
    </AuthLayout>
  )
}
