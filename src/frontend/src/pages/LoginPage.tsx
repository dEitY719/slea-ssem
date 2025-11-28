// REQ: REQ-F-A1-1, REQ-F-A1-2
import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageLayout } from '../components'
import { isAuthenticated } from '../utils/auth'
import './LoginPage.css'

/**
 * LoginPage - Auto-redirect to IDP or /home
 *
 * REQ-F-A1-1: Check cookie, redirect to IDP if not authenticated
 * REQ-F-A1-2: Redirect to /home if already authenticated
 */
const LoginPage: React.FC = () => {
  const navigate = useNavigate()
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const handleAutoRedirect = async () => {
      try {
        // REQ-F-A1-2: Check if already authenticated
        const authenticated = await isAuthenticated()

        if (authenticated) {
          // Already logged in, redirect to home
          navigate('/home', { replace: true })
          return
        }

        // MOCK MODE: Bypass IDP and go directly to home
        const mockSSO = import.meta.env.VITE_MOCK_SSO === 'true'
        if (mockSSO) {
          console.log('[MOCK SSO] Bypassing IDP, redirecting to home')
          navigate('/home', { replace: true })
          return
        }

        // REQ-F-A1-1: Redirect to IDP authorize URL
        const authUrl = buildIDPAuthUrl()

        // Redirect to IDP
        window.location.href = authUrl
      } catch (error) {
        console.error('Auto-redirect failed:', error)
        setIsLoading(false)
      }
    }

    handleAutoRedirect()
  }, [navigate])

  if (isLoading) {
    return (
      <PageLayout mainClassName="login-page" containerClassName="login-container">
        <div data-testid="login-container">
          <h1 className="login-title">SLEA-SSEM</h1>
          <p>인증 중...</p>
        </div>
      </PageLayout>
    )
  }

  return (
    <PageLayout mainClassName="login-page" containerClassName="login-container">
      <div data-testid="login-container">
        <h1 className="login-title">SLEA-SSEM</h1>
        <p>로그인 처리 중 오류가 발생했습니다.</p>
      </div>
    </PageLayout>
  )
}

/**
 * Build IDP authorization URL
 * @returns Authorization URL
 */
function buildIDPAuthUrl(): string {
  // TODO: Implement IDP authorization URL construction
  return ''
}

export default LoginPage
