import { BrowserRouter, Routes, Route } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import CallbackPage from './pages/CallbackPage'
import HomePage from './pages/HomePage'
import SignupPage from './pages/SignupPage'
import NicknameSetupPage from './pages/NicknameSetupPage'
import SelfAssessmentPage from './pages/SelfAssessmentPage'
import ProfileReviewPage from './pages/ProfileReviewPage'
import TestPage from './pages/TestPage'
import TestResultsPage from './pages/TestResultsPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/auth/callback" element={<CallbackPage />} />
        <Route path="/home" element={<HomePage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/nickname-setup" element={<NicknameSetupPage />} />
        <Route path="/self-assessment" element={<SelfAssessmentPage />} />
        <Route path="/profile-review" element={<ProfileReviewPage />} />
        <Route path="/test" element={<TestPage />} />
        <Route path="/test-results" element={<TestResultsPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
