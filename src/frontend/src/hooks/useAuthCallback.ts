// REQ: REQ-F-A1-4, REQ-F-A1-5
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { retrievePKCEParams, clearPKCEParams } from '../utils/pkce'

interface UseAuthCallbackResult {
  loading: boolean
  error: string | null
}

/**
 * Custom hook for handling OIDC authentication callback with PKCE
 *
 * REQ-F-A1-4: Receives authorization code and sends it with code_verifier to backend
 * REQ-F-A1-5: Receives HttpOnly JWT cookie and redirects to /home
 *
 * Flow:
 * 1. Extract code and state from URL
 * 2. Retrieve PKCE params from sessionStorage
 * 3. Verify state (CSRF protection)
 * 4. Call POST /api/auth/oidc/callback with { code, code_verifier, nonce }
 * 5. Receive HttpOnly cookie with JWT
 * 6. Clear PKCE params from sessionStorage
 * 7. Redirect to /home
 *
 * @param searchParams - URL search parameters from callback URL
 * @returns Object with loading and error states
 */
export function useAuthCallback(searchParams: URLSearchParams): UseAuthCallbackResult {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Step 1: Extract authorization code and state from URL
        const code = searchParams.get('code')
        const state = searchParams.get('state')

        if (!code) {
          setError('인증 코드가 누락되었습니다.')
          setLoading(false)
          return
        }

        if (!state) {
          setError('State 파라미터가 누락되었습니다.')
          setLoading(false)
          return
        }

        // Step 2: Retrieve PKCE params from sessionStorage
        const pkceParams = retrievePKCEParams()

        if (!pkceParams) {
          setError('인증 정보가 만료되었습니다. 다시 로그인해주세요.')
          setLoading(false)
          return
        }

        // Step 3: Verify state (CSRF protection)
        if (state !== pkceParams.state) {
          setError('잘못된 요청입니다. (State mismatch)')
          setLoading(false)
          return
        }

        // Step 4: Call backend OIDC callback API
        const response = await fetch('/api/auth/oidc/callback', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include', // REQ-F-A1-5: Include HttpOnly cookies
          body: JSON.stringify({
            code: code,
            code_verifier: pkceParams.codeVerifier,
            nonce: pkceParams.nonce,
          }),
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}))
          const errorMessage =
            errorData.detail || '로그인에 실패했습니다. 다시 시도해주세요.'
          setError(errorMessage)
          setLoading(false)
          return
        }

        // Step 5: Backend sets HttpOnly cookie automatically via Set-Cookie header
        // No need to manually handle the cookie - browser does it automatically

        // Step 6: Clear PKCE params from sessionStorage
        clearPKCEParams()

        // Step 7: Redirect to home page (REQ-F-A1-5)
        navigate('/home', { replace: true })
      } catch (err) {
        console.error('OIDC callback error:', err)
        setError(
          err instanceof Error ? err.message : '로그인 처리 중 오류가 발생했습니다.'
        )
        setLoading(false)
      }
    }

    handleCallback()
  }, [searchParams, navigate])

  return { loading, error }
}
