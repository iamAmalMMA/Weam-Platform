import { Navigate, Route, Routes } from 'react-router-dom'
import AppShell from './components/AppShell'
import ProtectedRoute from './components/ProtectedRoute'
import AiAssistantPage from './pages/AiAssistantPage'
import AdminDashboardPage from './pages/AdminDashboardPage'
import CareTeamPage from './pages/CareTeamPage'
import CenterDetailsPage from './pages/CenterDetailsPage'
import CentersPage from './pages/CentersPage'
import CenterMatchingPage from './pages/CenterMatchingPage'
import CenterManagementPage from './pages/CenterManagementPage'
import CommunicationHubPage from './pages/CommunicationHubPage'
import ChildDetailPage from './pages/ChildDetailPage'
import DashboardPage from './pages/DashboardPage'
import FollowUpsPage from './pages/FollowUpsPage'
import GoalsPage from './pages/GoalsPage'
import HomePage from './pages/HomePage'
import InvitationsPage from './pages/InvitationsPage'
import LoginPage from './pages/LoginPage'
import MessagesInboxPage from './pages/MessagesInboxPage'
import NewChildPage from './pages/NewChildPage'
import NotificationsPage from './pages/NotificationsPage'
import ProviderDashboardPage from './pages/ProviderDashboardPage'
import RegisterPage from './pages/RegisterPage'
import ReportAIPage from './pages/ReportAIPage'
import ReportsPage from './pages/ReportsPage'
import TimelinePage from './pages/TimelinePage'
import VoiceNotesPage from './pages/VoiceNotesPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/notifications" element={<NotificationsPage />} />
          <Route path="/provider" element={<ProviderDashboardPage />} />
          <Route path="/provider/center" element={<CenterManagementPage />} />
          <Route path="/admin" element={<AdminDashboardPage />} />
          <Route path="/invitations" element={<InvitationsPage />} />
          <Route path="/messages" element={<MessagesInboxPage />} />
          <Route path="/centers" element={<CentersPage />} />
          <Route path="/centers/:centerId" element={<CenterDetailsPage />} />
          <Route path="/children/new" element={<NewChildPage />} />
          <Route path="/children/:childId" element={<ChildDetailPage />} />
          <Route path="/children/:childId/care-team" element={<CareTeamPage />} />
          <Route path="/children/:childId/reports" element={<ReportsPage />} />
          <Route path="/children/:childId/goals" element={<GoalsPage />} />
          <Route path="/children/:childId/follow-ups" element={<FollowUpsPage />} />
          <Route path="/children/:childId/timeline" element={<TimelinePage />} />
          <Route path="/children/:childId/voice-notes" element={<VoiceNotesPage />} />
          <Route path="/children/:childId/communication" element={<CommunicationHubPage />} />
          <Route path="/children/:childId/assistant" element={<AiAssistantPage />} />
          <Route path="/children/:childId/center-matches" element={<CenterMatchingPage />} />
          <Route path="/reports/:reportId/ai" element={<ReportAIPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
