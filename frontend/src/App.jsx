import { Navigate, Route, Routes } from 'react-router-dom'
import ProtectedRoute from './components/common/ProtectedRoute.jsx'
import DashboardLayout from './layouts/DashboardLayout.jsx'
import LoginPage from './pages/LoginPage.jsx'
import DashboardPage from './pages/DashboardPage.jsx'
import HallSelectionPage from './pages/HallSelectionPage.jsx'
import IssuesPage from './pages/IssuesPage.jsx'
import IssueDetailPage from './pages/IssueDetailPage.jsx'
import AnalyticsPage from './pages/AnalyticsPage.jsx'
import AdminUsersPage from './pages/AdminUsersPage.jsx'
import AdminHallsPage from './pages/AdminHallsPage.jsx'
import AdminCategoriesPage from './pages/AdminCategoriesPage.jsx'
import ForgotPasswordPage from './pages/ForgotPasswordPage.jsx'
import SetSecurityQuestionPage from './pages/SetSecurityQuestionPage.jsx'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<DashboardLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/hall-selection" element={<HallSelectionPage />} />
          <Route path="/issues" element={<IssuesPage />} />
          <Route path="/issues/:issueId" element={<IssueDetailPage />} />
          <Route element={<ProtectedRoute allowedRoles={['admin']} />}>
            <Route path="/admin/users" element={<AdminUsersPage />} />
            <Route path="/admin/halls" element={<AdminHallsPage />} />
            <Route path="/admin/categories" element={<AdminCategoriesPage />} />
            <Route path="/set-security-question" element={<SetSecurityQuestionPage />} />
          </Route>
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

export default App
