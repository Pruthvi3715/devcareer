import { BrowserRouter, Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import AuditPage from './pages/AuditPage'
import ArchGraphPage from './pages/ArchGraphPage'
import CareerReportPage from './pages/CareerReportPage'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import ProfilePage from './pages/ProfilePage'
import ChatWidget from './components/ChatWidget'
import { AuthProvider } from './context/AuthContext'
export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/profile" element={<ProfilePage />} />
        <Route path="/audit/:auditId" element={<AuditPage />} />
        <Route path="/arch/:auditId" element={<ArchGraphPage />} />
        <Route path="/report/:auditId" element={<CareerReportPage />} />
        </Routes>
        {/* Floating chat widget — visible on every page when logged in */}
        <ChatWidget />
      </BrowserRouter>
    </AuthProvider>
  )
}