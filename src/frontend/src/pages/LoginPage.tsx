// REQ: REQ-F-A1-1, REQ-F-A1-2, REQ-F-A1-3
import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageLayout } from '../components'
import { isAuthenticated } from '../utils/auth'
import { generatePKCEParams, storePKCEParams } from '../utils/pkce'
import './LoginPage.css'

/**
 * LoginPage - Auto-redirect to OIDC or /home
 *
 * REQ-F-A1-1: Check cookie, generate PKCE if not authenticated
 * REQ-F-A1-2: Redirect to Azure AD with PKCE
 * REQ-F-A1-3: Redirect to /home if already authenticated
 */
const LoginPage: React.FC = () => {
  const navigate = useNavigate()
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const handleAutoRedirect = async () => {
      try {
        // REQ-F-A1-3: Check if already authenticated
        const authenticated = await isAuthenticated()

        if (authenticated) {
          // Already logged in, redirect to home
          navigate('/home', { replace: true })
          return
        }

        // MOCK MODE: Bypass Azure AD and go directly to callback
        const mockSSO = import.meta.env.VITE_MOCK_SSO === 'true'
        if (mockSSO) {
          console.log('[MOCK SSO] Bypassing Azure AD, redirecting to callback')
          navigate('/auth/callback', { replace: true })
          return
        }

        // REQ-F-A1-1: Generate PKCE parameters
        const pkceParams = await generatePKCEParams()

        // Store in sessionStorage for callback
        storePKCEParams({
          codeVerifier: pkceParams.codeVerifier,
          state: pkceParams.state,
          nonce: pkceParams.nonce,
        })

        // REQ-F-A1-2: Build Azure AD authorization URL
        const authUrl = buildAzureADAuthUrl(
          pkceParams.codeChallenge,
          pkceParams.state,
          pkceParams.nonce
        )

        // Redirect to Azure AD
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
 * Build Azure AD authorization URL with PKCE
 * @param codeChallenge - PKCE code_challenge
 * @param state - CSRF protection state
 * @param nonce - Replay attack protection nonce
 * @returns Authorization URL
 */
function buildAzureADAuthUrl(codeChallenge: string, state: string, nonce: string): string {
  const tenantId = import.meta.env.VITE_AZURE_AD_TENANT_ID || 'common'
  const clientId = import.meta.env.VITE_AZURE_AD_CLIENT_ID || ''
  const redirectUri = `${window.location.origin}/auth/callback`

  const params = new URLSearchParams({
    client_id: clientId,
    response_type: 'code',
    redirect_uri: redirectUri,
    scope: 'openid profile email',
    code_challenge: codeChallenge,
    code_challenge_method: 'S256',
    state: state,
    nonce: nonce,
  })

  return `https://login.microsoftonline.com/${tenantId}/oauth2/v2.0/authorize?${params.toString()}`
}

export default LoginPage
