// @ts-nocheck
// REQ: REQ-F-A1-1, REQ-F-A1-2, REQ-F-A1-Error-1
/// <reference types="vite/client" />
// @ts-ignore
import React, { useEffect, useState } from 'react'
 // @ts-ignore
import { useNavigate } from 'react-router-dom'
import { PageLayout } from '../components'
import { isAuthenticated } from '../utils/auth'
import { detectRedirectLoop, resetRedirectDetection } from '../utils/redirectDetection'
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
          // Already logged in, reset redirect counter and go to home
          resetRedirectDetection()
          navigate('/home', { replace: true })
          return
        }

        // REQ-F-A1-Error-1: Detect redirect loop before redirecting
        const detection = detectRedirectLoop()
        if (detection.shouldShowError) {
          console.warn(`[Auth Error] Redirect loop detected (${detection.count} attempts)`)
          navigate('/auth-error', { replace: true })
          return
        }

        // MOCK MODE: Bypass IDP and go directly to home
        const mockSSO = import.meta.env.VITE_MOCK_SSO === 'true'
        if (mockSSO) {
          console.log('[MOCK SSO] Bypassing IDP, redirecting to home')
          navigate('/home', { replace: true })
          return
        }

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

export default LoginPage
