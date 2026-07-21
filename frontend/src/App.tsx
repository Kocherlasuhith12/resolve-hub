import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth/useAuth'
import { AppShell } from './pages/AppShell'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { VerifyEmailPage } from './pages/VerifyEmailPage'
import './App.css'

function ProtectedRoute() {
  const { status } = useAuth()

  if (status === 'loading') {
    return (
      <main className="centered-page" aria-live="polite">
        <div className="loading-mark" aria-hidden="true" />
        <p>Restoring your workspace…</p>
      </main>
    )
  }

  return status === 'authenticated' ? <AppShell /> : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/verify-email" element={<VerifyEmailPage />} />
      <Route path="/" element={<ProtectedRoute />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
