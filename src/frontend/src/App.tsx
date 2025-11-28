import { BrowserRouter, Routes, Route } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import HomePage from './pages/HomePage'
import SignupPage from './pages/SignupPage'
import ConsentPage from './pages/ConsentPage'
import NicknameSetupPage from './pages/NicknameSetupPage'
import CareerInfoPage from './pages/CareerInfoPage'
import SelfAssessmentPage from './pages/SelfAssessmentPage'
import ProfileReviewPage from './pages/ProfileReviewPage'
import ProfileEditPage from './pages/ProfileEditPage'
import TestPage from './pages/TestPage'
import TestResultsPage from './pages/TestResultsPage'
import ExplanationPage from './pages/ExplanationPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/home" element={<HomePage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/consent" element={<ConsentPage />} />
        <Route path="/nickname-setup" element={<NicknameSetupPage />} />
        <Route path="/career-info" element={<CareerInfoPage />} />
        <Route path="/self-assessment" element={<SelfAssessmentPage />} />
        <Route path="/profile-review" element={<ProfileReviewPage />} />
        <Route path="/profile/edit" element={<ProfileEditPage />} />
        <Route path="/test" element={<TestPage />} />
        <Route path="/test-results" element={<TestResultsPage />} />
        <Route path="/test-explanations/:sessionId" element={<ExplanationPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
