// REQ: REQ-F-A1-Error-2, REQ-F-A1-Error-3
import React from 'react'
import { useNavigate } from 'react-router-dom'
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import { PageLayout } from '../components'
import { resetRedirectDetection } from '../utils/redirectDetection'
import './AuthErrorPage.css'

/**
 * AuthErrorPage - Display authentication error with troubleshooting steps
 *
 * REQ-F-A1-Error-2: Show clear error message and recommended actions
 * REQ-F-A1-Error-3: Provide "Try Again" button
 */
const AuthErrorPage: React.FC = () => {
  const navigate = useNavigate()

  const handleTryAgain = () => {
    // REQ-F-A1-Error-3: Reset redirect counter and try login again
    resetRedirectDetection()
    navigate('/', { replace: true })
  }

  return (
    <PageLayout mainClassName="auth-error-page" containerClassName="auth-error-container">
      <div className="auth-error-content">
        <ExclamationTriangleIcon className="error-icon-large" />

        <h1 className="error-title">로그인이 정상적으로 완료되지 않았습니다</h1>

        <p className="error-description">
          인증 과정에서 문제가 발생했습니다. 아래 권장 조치를 확인해주세요.
        </p>

        <div className="troubleshooting-section">
          <h2 className="troubleshooting-title">권장 조치</h2>
          <ul className="troubleshooting-list">
            <li>
              <strong>브라우저 쿠키 설정 확인</strong>
              <p>브라우저 설정에서 쿠키가 차단되어 있지 않은지 확인해주세요.</p>
            </li>
            <li>
              <strong>다른 브라우저로 시도</strong>
              <p>Chrome, Edge, Safari 등 다른 브라우저를 사용해보세요.</p>
            </li>
            <li>
              <strong>IT 헬프데스크 연락</strong>
              <p>문제가 계속되면 IT 헬프데스크에 문의해주세요.</p>
            </li>
          </ul>
        </div>

        <button className="try-again-button" onClick={handleTryAgain}>
          다시 시도
        </button>
      </div>
    </PageLayout>
  )
}

export default AuthErrorPage
