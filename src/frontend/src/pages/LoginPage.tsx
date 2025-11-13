// REQ: REQ-F-A1-1
import React from 'react'
import './LoginPage.css'

const LoginPage: React.FC = () => {
  const handleLogin = () => {
    // 개발 환경에서는 기본적으로 SSO mock 모드를 사용하지만,
    // VITE_MOCK_SSO 값을 통해 명시적으로 제어할 수 있다.
    const shouldMockSso =
      import.meta.env.VITE_MOCK_SSO === 'true' ||
      (import.meta.env.VITE_MOCK_SSO !== 'false' && import.meta.env.DEV)

    if (!shouldMockSso) {
      // 실제 SSO 페이지로 리다이렉트
      window.location.href = '/api/auth/sso/redirect'
      return
    }

    // SSO mock 모드: CallbackPage로 직접 이동하면서 SSO 시뮬레이션 파라미터 부여
    const mockSsoParams = new URLSearchParams({
      sso_mock: 'true',
      knox_id: import.meta.env.VITE_MOCK_SSO_KNOX_ID ?? 'mock_user_001',
      name: import.meta.env.VITE_MOCK_SSO_NAME ?? 'Mock User',
      dept: import.meta.env.VITE_MOCK_SSO_DEPT ?? 'Mock Department',
      business_unit: import.meta.env.VITE_MOCK_SSO_BU ?? 'S.LSI',
      email: import.meta.env.VITE_MOCK_SSO_EMAIL ?? 'mock.user@samsung.com',
    })

    const shouldMockApi = import.meta.env.VITE_MOCK_API === 'true'

    if (shouldMockApi) {
      // 백엔드 API mock을 사용할 때는 하위 호환성을 위해 기존 mock 플래그도 유지한다.
      mockSsoParams.set('api_mock', 'true')
      mockSsoParams.set('mock', 'true')
    }

    window.location.href = `/auth/callback?${mockSsoParams.toString()}`
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
