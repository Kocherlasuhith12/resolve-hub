import { NavLink } from 'react-router-dom'

export function AuthTabs() {
  return (
    <nav className="auth-tabs" aria-label="Account access">
      <NavLink to="/login">Sign in</NavLink>
      <NavLink to="/register">Create account</NavLink>
    </nav>
  )
}
