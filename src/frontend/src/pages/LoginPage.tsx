// REQ: REQ-F-A1-1
import React from 'react'
import './LoginPage.css'

const LoginPage: React.FC = () => {
  const handleLogin = () => {
    // 개발 환경에서는 mock 모드로 CallbackPage로 직접 이동
    // 실제 프로덕션에서는 Samsung AD SSO 페이지로 리다이렉트
    const isDevelopment = import.meta.env.DEV

    if (isDevelopment) {
      // 개발 모드: mock 데이터로 콜백 페이지 호출
      window.location.href = '/auth/callback?mock=true'
    } else {
      // 프로덕션: Samsung AD SSO 페이지로 리다이렉트
      window.location.href = '/api/auth/sso/redirect'
    }
  }

  return (
    <main className="login-page">
      <div className="login-container" data-testid="login-container">
        <h1 className="login-title">SLEA-SSEM</h1>
        <button
          type="button"
          className="login-button"
          onClick={handleLogin}
          aria-label="Samsung AD로 로그인"
        >
          Samsung AD로 로그인
        </button>
      </div>
    </main>
  )
}

export default LoginPage
