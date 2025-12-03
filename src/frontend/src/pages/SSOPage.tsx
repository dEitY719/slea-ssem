// @ts-nocheck
// REQ: REQ-F-A0-Landing, REQ-F-A1-1, REQ-F-A1-2, REQ-F-A1-Error-1
/// <reference types="vite/client" />
// @ts-ignore
import React, { useEffect, useState } from 'react'
 // @ts-ignore
import { useNavigate, useSearchParams } from 'react-router-dom'
import { PageLayout } from '../components'
import { authService } from '../services/authService'
import { setMockAuthState } from '../lib/transport/mockTransport'
import { detectRedirectLoop, resetRedirectDetection } from '../utils/redirectDetection'
import './SSOPage.css'

/**
 * SSOPage - Handle SSO authentication with IDP
 *
 * REQ-F-A0-Landing: SSO authentication page at /sso
 * REQ-F-A1-1: Check cookie, redirect to IDP if not authenticated
 * REQ-F-A1-2: Redirect to returnTo or / if already authenticated
 */
const SSOPage: React.FC = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const handleAutoRedirect = async () => {
      try {
        // REQ-F-A0-Landing: Get returnTo parameter
        const returnTo = searchParams.get('returnTo') || '/'

        // REQ-F-A1-2: Check if already authenticated
        const authStatus = await authService.getAuthStatus()

        if (authStatus.authenticated) {
          // Already logged in, reset redirect counter and go to returnTo
          resetRedirectDetection()
          console.log(`[SSO] Already authenticated, redirecting to ${returnTo}`)
          navigate(returnTo, { replace: true })
          return
        }

        // REQ-F-A1-Error-1: Detect redirect loop before redirecting
        const detection = detectRedirectLoop()
        if (detection.shouldShowError) {
          console.warn(`[Auth Error] Redirect loop detected (${detection.count} attempts)`)
          navigate('/auth-error', { replace: true })
          return
        }

        // MOCK MODE: Simulate SSO success
        const mockSSO = import.meta.env.VITE_MOCK_SSO === 'true'
        if (mockSSO) {
          console.log('[MOCK SSO] Simulating SSO authentication success')

          // REQ-F-A0-Landing: Simulate SSO authentication (set isAuthenticated = true)
          // Note: This does NOT set nickname - user may still need to sign up
          setMockAuthState(true, null)

          console.log(`[MOCK SSO] Authentication successful, redirecting to ${returnTo}`)
          navigate(returnTo, { replace: true })
          return
        }

        // REQ-F-A1-1: Redirect to IDP authorize URL
        const authUrl = buildIDPAuthUrl(returnTo)

        // Redirect to IDP
        window.location.href = authUrl
      } catch (error) {
        console.error('Auto-redirect failed:', error)
        setIsLoading(false)
      }
    }

    handleAutoRedirect()
  }, [navigate, searchParams])

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
 * REQ-F-A0-Landing: Include returnTo in state parameter
 *
 * @param returnTo - Path to return to after authentication
 * @returns Authorization URL
 */
function buildIDPAuthUrl(returnTo: string): string {
  // TODO: Implement IDP authorization URL construction
  // Should include returnTo in state parameter for SSO callback
  // Example: https://idp.example.com/authorize?client_id=...&state={returnTo: '/consent'}
  return ''
}

export default SSOPage
