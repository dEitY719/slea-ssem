// REQ: REQ-F-A1-2
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { saveToken } from '../utils/auth'
import { parseUserData } from '../utils/parseUserData'
import { authService, type LoginResponse } from '../services'
import { debugLog } from '../utils/logger'

interface UseAuthCallbackResult {
  loading: boolean
  error: string | null
}

/**
 * Custom hook for handling SSO authentication callback
 *
 * Handles:
 * - Mock mode for development/testing (supports ?api_mock=true & ?sso_mock=true)
 * - User data parsing from URL params
 * - Backend API authentication
 * - JWT token storage
 * - Navigation to home screen
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
        const isApiMock =
          searchParams.get('api_mock') === 'true' ||
          searchParams.get('mock') === 'true' ||
          import.meta.env.VITE_MOCK_API === 'true'
        const isSsoMock =
          searchParams.get('sso_mock') === 'true' || searchParams.get('mock') === 'true'

        let data: LoginResponse

        if (isApiMock) {
          // Mock mode: 백엔드 없이 프론트엔드만 테스트할 때 사용
          // 실제 API 호출 없이 mock 응답 반환
            debugLog('🎭 Mock mode: 백엔드 API 호출 생략 (api_mock)')

          // Save mock mode flag to localStorage to persist across page navigation
          localStorage.setItem('slea_ssem_api_mock', 'true')

          // Mock 응답 생성 (신규 사용자로 시뮬레이션)
          data = {
            access_token: 'mock_jwt_token_' + Date.now(),
            token_type: 'bearer',
            user_id: 'test_user_001',
            is_new_user: true, // 신규 사용자 시뮬레이션 (false로 변경하면 기존 사용자)
          }

          // 실제 API 호출처럼 약간의 딜레이 추가
          await new Promise((resolve) => setTimeout(resolve, 500))
        } else {
          // 실제 모드: 백엔드 API 호출 (Transport pattern 사용)
          let userData

          if (isSsoMock) {
            // SSO mock mode: 가짜 SSO 데이터를 생성하여 백엔드에 전달
            // 백엔드는 이를 처리하여 실제 JWT 토큰 반환
              debugLog('🎭 SSO mock mode: 가짜 SSO 데이터로 백엔드 호출')
            userData = {
              knox_id: 'test_mock_user_' + Date.now(),
              name: 'Test Mock User',
              dept: 'Engineering',
              business_unit: 'S.LSI',
              email: `test_mock_${Date.now()}@samsung.com`,
            }
          } else {
            // 실제 SSO 데이터를 URL 파라미터에서 파싱
            userData = parseUserData(searchParams)

            // Validate required parameters
            if (!userData) {
              setError('필수 정보가 누락되었습니다.')
              setLoading(false)
              return
            }
          }

          // Call backend authentication API using service layer
          data = await authService.login(userData)
        }

        // Save JWT token to localStorage
        saveToken(data.access_token)

        // REQ-F-A1-2: All users (new and existing) redirect to home screen
        navigate('/home')
      } catch (err) {
        console.error('Authentication error:', err)
        setError(
          err instanceof Error ? err.message : '로그인에 실패했습니다. 다시 시도해주세요.'
        )
        setLoading(false)
      }
    }

    handleCallback()
  }, [searchParams, navigate])

  return { loading, error }
}
