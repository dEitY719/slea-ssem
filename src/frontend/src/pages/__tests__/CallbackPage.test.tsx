// REQ: REQ-F-A1-2
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter, MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import CallbackPage from '../CallbackPage'

// Mock fetch API
global.fetch = vi.fn()

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

describe('CallbackPage - REQ-F-A1-2', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorageMock.clear()
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  // Test 1: Happy Path - 신규 사용자 로그인 성공 (home-first flow)
  it('should redirect to /home for new users after successful login', async () => {
    const mockResponse = {
      access_token: 'test_token_123',
      token_type: 'bearer',
      user_id: 'test_user_001',
      is_new_user: true,
    }

    ;(global.fetch as any).mockResolvedValueOnce({
      ok: true,
      status: 201,
      json: async () => mockResponse,
    })

    render(
      <MemoryRouter
        initialEntries={[
          '/auth/callback?knox_id=test_user_001&name=테스트&dept=개발팀&business_unit=S.LSI&email=test@samsung.com',
        ]}
      >
        <CallbackPage />
      </MemoryRouter>
    )

    // 로딩 표시 확인
    expect(screen.getByText(/로그인 처리 중/i)).toBeInTheDocument()

    // API 호출 대기
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/auth/login'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: expect.stringContaining('test_user_001'),
        })
      )
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
    const mockResponse = {
      access_token: 'existing_user_token_456',
      token_type: 'bearer',
      user_id: 'existing_user_002',
      is_new_user: false,
    }

    ;(global.fetch as any).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockResponse,
    })

    render(
      <MemoryRouter
        initialEntries={[
          '/auth/callback?knox_id=existing_user_002&name=기존사용자&dept=개발팀&business_unit=S.LSI&email=existing@samsung.com',
        ]}
      >
        <CallbackPage />
      </MemoryRouter>
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
    ;(global.fetch as any).mockRejectedValueOnce(new Error('Network error'))

    render(
      <MemoryRouter
        initialEntries={[
          '/auth/callback?knox_id=test_user_003&name=테스트&dept=개발팀&business_unit=S.LSI&email=test3@samsung.com',
        ]}
      >
        <CallbackPage />
      </MemoryRouter>
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
    ;(global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ detail: 'Authentication failed' }),
    })

    render(
      <MemoryRouter
        initialEntries={[
          '/auth/callback?knox_id=test_user_004&name=테스트&dept=개발팀&business_unit=S.LSI&email=test4@samsung.com',
        ]}
      >
        <CallbackPage />
      </MemoryRouter>
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
  it('should use mock response without API call when mock=true', async () => {
    render(
      <MemoryRouter initialEntries={['/auth/callback?mock=true']}>
        <CallbackPage />
      </MemoryRouter>
    )

    // Mock 모드에서는 API 호출이 발생하지 않아야 함
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/home')
    })

    // fetch가 호출되지 않았는지 확인
    expect(global.fetch).not.toHaveBeenCalled()

    // 토큰이 저장되었는지 확인
    expect(localStorageMock.getItem('slea_ssem_token')).toMatch(/^mock_jwt_token_/)
  })

  // Test 6: Performance - 3초 이내 리다이렉트
  it('should redirect within 3 seconds after successful authentication', async () => {
    const startTime = Date.now()
    const mockResponse = {
      access_token: 'fast_token',
      token_type: 'bearer',
      user_id: 'fast_user',
      is_new_user: false,
    }

    ;(global.fetch as any).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockResponse,
    })

    render(
      <MemoryRouter
        initialEntries={[
          '/auth/callback?knox_id=fast_user&name=Fast&dept=Dev&business_unit=S.LSI&email=fast@samsung.com',
        ]}
      >
        <CallbackPage />
      </MemoryRouter>
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
    render(
      <MemoryRouter initialEntries={['/auth/callback']}>
        <CallbackPage />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/필수 정보가 누락되었습니다/i)).toBeInTheDocument()
    })
  })

  // Test 8: Acceptance Criteria - 로딩 스피너 표시
  it('should display loading spinner during authentication', () => {
    ;(global.fetch as any).mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          setTimeout(
            () =>
              resolve({
                ok: true,
                json: async () => ({
                  access_token: 'token',
                  is_new_user: true,
                }),
              }),
            1000
          )
        })
    )

    render(
      <MemoryRouter
        initialEntries={[
          '/auth/callback?knox_id=test&name=Test&dept=Dev&business_unit=S.LSI&email=test@samsung.com',
        ]}
      >
        <CallbackPage />
      </MemoryRouter>
    )

    // 로딩 상태 표시 확인
    expect(screen.getByText(/로그인 처리 중/i)).toBeInTheDocument()
  })
})
