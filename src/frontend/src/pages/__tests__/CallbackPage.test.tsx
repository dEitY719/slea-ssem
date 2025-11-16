// REQ: REQ-F-A1-2
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import CallbackPage from '../CallbackPage'
import {
  mockConfig,
  setMockData,
  setMockError,
  clearMockErrors,
  clearMockRequests,
  getMockRequests,
} from '../../lib/transport'

const AUTH_ENDPOINT = '/api/auth/login'

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString()
    },
    removeItem: (key: string) => {
      delete store[key]
    },
    clear: () => {
      store = {}
    },
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

// Mock useNavigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

const renderWithRoute = (path: string) =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <CallbackPage />
    </MemoryRouter>
  )

const getLoginRequests = () =>
  getMockRequests({
    url: AUTH_ENDPOINT,
    method: 'POST',
  })

describe('CallbackPage - REQ-F-A1-2', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockReset()
    localStorageMock.clear()
    localStorageMock.setItem('slea_ssem_api_mock', 'true')
    mockConfig.delay = 0
    mockConfig.simulateError = false
    mockConfig.slowNetwork = false
    clearMockErrors()
    clearMockRequests()
    setMockData(AUTH_ENDPOINT, {
      access_token: 'default_token',
      token_type: 'bearer',
      user_id: 'default_user',
      is_new_user: true,
    })
  })

  afterEach(() => {
    clearMockErrors()
    clearMockRequests()
    mockConfig.delay = 0
    mockConfig.simulateError = false
    mockConfig.slowNetwork = false
  })

  // Test 1: Happy Path - 신규 사용자 로그인 성공 (home-first flow)
  it('should redirect to /home for new users after successful login', async () => {
    setMockData(AUTH_ENDPOINT, {
      access_token: 'test_token_123',
      token_type: 'bearer',
      user_id: 'test_user_001',
      is_new_user: true,
    })

    renderWithRoute(
      '/auth/callback?knox_id=test_user_001&name=테스트&dept=개발팀&business_unit=S.LSI&email=test@samsung.com'
    )

    // 로딩 표시 확인
    expect(screen.getByText(/로그인 처리 중/i)).toBeInTheDocument()

    // API 호출 확인
    await waitFor(() => {
      const requests = getLoginRequests()
      expect(requests).toHaveLength(1)
      expect(requests[0].body).toMatchObject({
        knox_id: 'test_user_001',
        name: '테스트',
        dept: '개발팀',
        business_unit: 'S.LSI',
        email: 'test@samsung.com',
      })
    })

    // 토큰 저장 확인
    await waitFor(() => {
      expect(localStorageMock.getItem('slea_ssem_token')).toBe('test_token_123')
    })

    // /home으로 리다이렉트 확인 (home-first approach)
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/home')
    })
  })

  // Test 2: Happy Path - 기존 사용자 로그인 성공 (home-first flow)
  it('should redirect to /home for existing users after successful login', async () => {
    setMockData(AUTH_ENDPOINT, {
      access_token: 'existing_user_token_456',
      token_type: 'bearer',
      user_id: 'existing_user_002',
      is_new_user: false,
    })

    renderWithRoute(
      '/auth/callback?knox_id=existing_user_002&name=기존사용자&dept=개발팀&business_unit=S.LSI&email=existing@samsung.com'
    )

    // 토큰 저장 확인
    await waitFor(() => {
      expect(localStorageMock.getItem('slea_ssem_token')).toBe('existing_user_token_456')
    })

    // /home으로 리다이렉트 확인 (home-first approach)
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/home')
    })
  })

  // Test 3: Edge Case - API 호출 실패
  it('should display error message when API call fails', async () => {
    setMockError(AUTH_ENDPOINT, 'Network error')

    renderWithRoute(
      '/auth/callback?knox_id=test_user_003&name=테스트&dept=개발팀&business_unit=S.LSI&email=test3@samsung.com'
    )

    // 에러 메시지 표시 확인
    await waitFor(() => {
      expect(screen.getByText(/Network error/i)).toBeInTheDocument()
    })

    // 로딩 스피너가 사라짐
    expect(screen.queryByText(/로그인 처리 중/i)).not.toBeInTheDocument()
  })

  // Test 4: Acceptance Criteria - 에러 링크 표시
  it('should display help links when authentication fails', async () => {
    setMockError(AUTH_ENDPOINT, 'Authentication failed')

    renderWithRoute(
      '/auth/callback?knox_id=test_user_004&name=테스트&dept=개발팀&business_unit=S.LSI&email=test4@samsung.com'
    )

    await waitFor(() => {
      // "계정 정보 확인" 링크
      const accountLink = screen.getByRole('link', { name: /계정 정보 확인/i })
      expect(accountLink).toBeInTheDocument()
      expect(accountLink).toHaveAttribute('href', expect.stringContaining('account'))

      // "관리자 문의" 링크
      const supportLink = screen.getByRole('link', { name: /관리자 문의/i })
      expect(supportLink).toBeInTheDocument()
      expect(supportLink).toHaveAttribute('href', expect.stringContaining('support'))
    })
  })

  // Test 5: Acceptance Criteria - Mock 모드 (home-first flow)
  it('should use mock response without API call when api_mock=true', async () => {
    localStorageMock.clear()

    renderWithRoute('/auth/callback?api_mock=true')

    // Mock 모드에서는 API 호출이 발생하지 않아야 함
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/home')
    })

    // transport 요청이 없는지 확인
    expect(getLoginRequests()).toHaveLength(0)

    // 토큰이 저장되었는지 확인
    expect(localStorageMock.getItem('slea_ssem_token')).toMatch(/^mock_jwt_token_/)
    expect(localStorageMock.getItem('slea_ssem_api_mock')).toBe('true')
  })

  it('should continue to support legacy mock=true parameter', async () => {
    localStorageMock.clear()

    renderWithRoute('/auth/callback?mock=true')

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/home')
    })

    expect(localStorageMock.getItem('slea_ssem_token')).toMatch(/^mock_jwt_token_/)
  })

  // Test 5.5: SSO mock mode - 가짜 SSO 데이터로 백엔드 호출하여 실제 JWT 받기
  it('should call backend with fake SSO data when sso_mock=true', async () => {
    setMockData(AUTH_ENDPOINT, {
      access_token: 'real_jwt_token_from_backend',
      token_type: 'bearer',
      user_id: 'mock_user_123',
      is_new_user: true,
    })

    renderWithRoute('/auth/callback?sso_mock=true')

    // 백엔드 API가 호출되어야 함
      await waitFor(() => {
        const requests = getLoginRequests()
        expect(requests).toHaveLength(1)
        expect(requests[0].body?.knox_id).toMatch(/^test_mock_user_/)
      })

    // 백엔드에서 받은 실제 JWT 토큰이 저장되어야 함
    await waitFor(() => {
      expect(localStorageMock.getItem('slea_ssem_token')).toBe('real_jwt_token_from_backend')
    })

    // 테스트에서는 mock 모드를 유지하고 있으므로 플래그가 변경되지 않아야 함
    expect(localStorageMock.getItem('slea_ssem_api_mock')).toBe('true')

    // /home으로 리다이렉트
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/home')
    })
  })

  // Test 6: Performance - 3초 이내 리다이렉트
  it('should redirect within 3 seconds after successful authentication', async () => {
    const startTime = Date.now()
    setMockData(AUTH_ENDPOINT, {
      access_token: 'fast_token',
      token_type: 'bearer',
      user_id: 'fast_user',
      is_new_user: false,
    })

    renderWithRoute(
      '/auth/callback?knox_id=fast_user&name=Fast&dept=Dev&business_unit=S.LSI&email=fast@samsung.com'
    )

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalled()
    })

    const endTime = Date.now()
    const elapsed = endTime - startTime

    // 3초(3000ms) 이내에 리다이렉트
    expect(elapsed).toBeLessThan(3000)
  })

  // Test 7: Edge Case - 필수 파라미터 누락
  it('should display error when required parameters are missing', async () => {
    renderWithRoute('/auth/callback')

    await waitFor(() => {
      expect(screen.getByText(/필수 정보가 누락되었습니다/i)).toBeInTheDocument()
    })
  })

  // Test 8: Acceptance Criteria - 로딩 스피너 표시
  it('should display loading spinner during authentication', () => {
    mockConfig.delay = 1000
    setMockData(AUTH_ENDPOINT, {
      access_token: 'token',
      token_type: 'bearer',
      user_id: 'test',
      is_new_user: true,
    })

    renderWithRoute(
      '/auth/callback?knox_id=test&name=Test&dept=Dev&business_unit=S.LSI&email=test@samsung.com'
    )

    // 로딩 상태 표시 확인
    expect(screen.getByText(/로그인 처리 중/i)).toBeInTheDocument()
  })
})
