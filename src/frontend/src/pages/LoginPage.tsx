// @ts-nocheck
// REQ: REQ-F-A0-Landing
/// <reference types="vite/client" />
// @ts-ignore
import React, { useEffect, useState } from 'react'
// @ts-ignore
import { useNavigate } from 'react-router-dom'
import { PageLayout } from '../components'
import { authService } from '../services/authService'
import './SSOPage.css'

/**
 * LoginPage - Handle login button flow
 *
 * Flow:
 * 1. Call POST /api/auth/login (Private-Auth API)
 * 2. If 401 (no SSO) → transport redirects to /sso?returnTo=/login
 * 3. SSO success → redirects back to /login
 * 4. Auto-retry login API
 * 5. If 403 NEED_SIGNUP → transport redirects to /signup
 * 6. If success → navigate to /home
 */
const LoginPage: React.FC = () => {
  const navigate = useNavigate()
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const performLogin = async () => {
      try {
        // Call login API (Private-Auth)
        // Backend checks: SSO authentication → membership status
        // - If no SSO (401) → transport redirects to /sso?returnTo=/login
        // - If not member (403) → transport redirects to /signup?returnTo=/login
        // - If success → proceed to home
        await authService.login({} as any)

        // Success: user is authenticated and member
        console.log('[Login] Login successful, navigating to /home')
        navigate('/home', { replace: true })
      } catch (err) {
        // Unexpected errors only (401/403 are handled by transport)
        console.error('[Login] Login failed:', err)
        setError(err instanceof Error ? err.message : 'Login failed')
        setIsLoading(false)
      }
    }

    performLogin()
  }, [navigate])

  if (error) {
    return (
      <PageLayout mainClassName="login-page" containerClassName="login-container">
        <div data-testid="login-container">
          <h1 className="login-title">SLEA-SSEM</h1>
          <p>로그인 처리 중 오류가 발생했습니다.</p>
          <p>{error}</p>
        </div>
      </PageLayout>
    )
  }

  return (
    <PageLayout mainClassName="login-page" containerClassName="login-container">
      <div data-testid="login-container">
        <h1 className="login-title">SLEA-SSEM</h1>
        <p>로그인 중...</p>
      </div>
    </PageLayout>
  )
}

export default LoginPage
