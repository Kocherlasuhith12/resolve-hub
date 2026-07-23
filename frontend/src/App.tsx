import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth/useAuth'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { VerifyEmailPage } from './pages/VerifyEmailPage'
import { TenantSetupPage } from './pages/TenantSetupPage'
import { AppLayout } from './layouts/AppLayout'
import { DashboardPage } from './pages/DashboardPage'
import { RequestsPage } from './pages/RequestsPage'
import { IncidentsPage } from './pages/IncidentsPage'
import { ProblemsPage } from './pages/ProblemsPage'
import { ChangesPage } from './pages/ChangesPage'
import { AssetsPage } from './pages/AssetsPage'
import { KnowledgePage } from './pages/KnowledgePage'
import { AiCopilotPage } from './pages/AiCopilotPage'
import { AnalyticsPage } from './pages/AnalyticsPage'
import { NotificationsPage } from './pages/NotificationsPage'
import { AdministrationPage } from './pages/AdministrationPage'
import { ProfilePage } from './pages/ProfilePage'
import { WorkspaceSettingsPage } from './pages/WorkspaceSettingsPage'
import { AppearancePage } from './pages/AppearancePage'
import { SystemSettingsPage } from './pages/SystemSettingsPage'
import { BillingPage } from './pages/BillingPage'
import { HelpSupportPage } from './pages/HelpSupportPage'
import { ActivityPage } from './pages/ActivityPage'
import { AuditLogsPage } from './pages/AuditLogsPage'
import './App.css'

function ProtectedRoute({ element }: { element: React.ReactNode }) {
  const { status } = useAuth()

  if (status === 'loading') {
    return (
      <main className="centered-page" aria-live="polite">
        <div className="loading-mark" aria-hidden="true" />
        <p>Restoring your workspace…</p>
      </main>
    )
  }

  return status === 'authenticated' ? <>{element}</> : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      {/* Public Auth Routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/verify-email" element={<VerifyEmailPage />} />

      {/* Initial Tenant Onboarding Route */}
      <Route path="/setup-workspace" element={<ProtectedRoute element={<TenantSetupPage />} />} />

      {/* Protected Enterprise Layout & Routes */}
      <Route element={<ProtectedRoute element={<AppLayout />} />}>
        <Route path="/" element={<Navigate to="/requests" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/requests" element={<RequestsPage />} />
        <Route path="/incidents" element={<IncidentsPage />} />
        <Route path="/problems" element={<ProblemsPage />} />
        <Route path="/changes" element={<ChangesPage />} />
        <Route path="/assets" element={<AssetsPage />} />
        <Route path="/knowledge" element={<KnowledgePage />} />
        <Route path="/copilot" element={<AiCopilotPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/notifications" element={<NotificationsPage />} />
        <Route path="/administration" element={<AdministrationPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/settings" element={<WorkspaceSettingsPage />} />
        <Route path="/settings/workspace" element={<WorkspaceSettingsPage />} />
        <Route path="/settings/appearance" element={<AppearancePage />} />
        <Route path="/settings/system" element={<SystemSettingsPage />} />
        <Route path="/settings/billing" element={<BillingPage />} />
        <Route path="/help" element={<HelpSupportPage />} />
        <Route path="/activity" element={<ActivityPage />} />
        <Route path="/audit-logs" element={<AuditLogsPage />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
