// REQ: REQ-F-A1-2, REQ-F-A2-1, REQ-F-A3
import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getToken } from '../utils/auth'
import { useUserProfile } from '../hooks/useUserProfile'
import './HomePage.css'

const HomePage: React.FC = () => {
  const navigate = useNavigate()
  const { checkNickname } = useUserProfile()
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const handleStart = async () => {
    // REQ-F-A2-1: Check if user has set nickname before proceeding
    try {
      const currentNickname = await checkNickname()

      if (currentNickname === null) {
        // User hasn't set nickname yet, redirect to nickname setup
        navigate('/nickname-setup')
      } else {
        // User has nickname, proceed to self-assessment
        // REQ-F-A2-2-1: Navigate to /self-assessment
        // TODO: When profile check API is available, check if user has completed profile
        // and navigate to /test if profile exists
        navigate('/self-assessment')
      }
    } catch (err) {
      // Log detailed error for debugging
      console.error('Failed to check user profile:', err)

      // Show user-friendly error message with hint
      const errorMsg = err instanceof Error ? err.message : 'Unknown error'
      setErrorMessage(`프로필 정보를 불러오는데 실패했습니다: ${errorMsg}`)
    }
  }

  // Verify user is authenticated
  const token = getToken()
  if (!token) {
    navigate('/')
    return null
  }

  return (
    <main className="home-page">
      <div className="home-container">
        <h1 className="home-title">S.LSI Learning Platform</h1>
        <p className="home-description">
          AI 기반 학습 플랫폼에 오신 것을 환영합니다.
        </p>
        <p className="home-subtitle">
          개인 맞춤형 레벨 테스트로 학습을 시작하세요.
        </p>
        {errorMessage && (
          <p className="error-message" style={{ color: '#d32f2f', marginBottom: '1rem' }}>
            {errorMessage}
          </p>
        )}
        <button className="start-button" onClick={handleStart}>
          시작하기
        </button>
      </div>
    </main>
  )
}

export default HomePage
