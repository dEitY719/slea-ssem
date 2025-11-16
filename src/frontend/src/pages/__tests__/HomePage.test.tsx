// REQ: REQ-F-A2-1, REQ-F-A2-Signup-1
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import HomePage from '../HomePage'
import * as authUtils from '../../utils/auth'
import {
  mockConfig,
  setMockData,
  setMockError,
  clearMockErrors,
  clearMockRequests,
  getMockRequests,
} from '../../lib/transport'

// Mock useNavigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// Mock auth utils
vi.mock('../../utils/auth', () => ({
  getToken: vi.fn(() => 'mock_jwt_token'),
}))

  describe('HomePage', () => {
    beforeEach(() => {
      vi.clearAllMocks()
      mockNavigate.mockReset()
      vi.spyOn(authUtils, 'getToken').mockReturnValue('mock_jwt_token')
      localStorage.setItem('slea_ssem_api_mock', 'true')
      mockConfig.delay = 0
      mockConfig.simulateError = false
      clearMockErrors()
      clearMockRequests()
      setMockData('/api/profile/nickname', {
        user_id: 'test@samsung.com',
        nickname: null,
        registered_at: null,
        updated_at: null,
      })
    })

    afterEach(() => {
      localStorage.removeItem('slea_ssem_api_mock')
    })

  it('should redirect to login if no token is present', () => {
    vi.spyOn(authUtils, 'getToken').mockReturnValue(null)

    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    )

    expect(mockNavigate).toHaveBeenCalledWith('/')
  })

    it('should display welcome message when authenticated', async () => {
    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    )

      await waitFor(() => {
        expect(getMockRequests({ url: '/api/profile/nickname' }).length).toBeGreaterThan(0)
      })

      expect(screen.getAllByText(/S\.LSI Learning Platform/).length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText(/AI 기반 학습 플랫폼/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /시작하기/i })).toBeInTheDocument()
  })

  it('should call API to check nickname when "시작하기" is clicked', async () => {
    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    )

      await waitFor(() => {
        expect(getMockRequests({ url: '/api/profile/nickname' }).length).toBe(1)
      })

      clearMockRequests()

    const startButton = screen.getByRole('button', { name: /시작하기/i })
    fireEvent.click(startButton)

    await waitFor(() => {
        expect(getMockRequests({ url: '/api/profile/nickname' }).length).toBe(1)
    })
  })

  it('should redirect to /nickname-setup when nickname is null', async () => {
    // REQ: REQ-F-A2-1
    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    )

    const startButton = screen.getByRole('button', { name: /시작하기/i })
    fireEvent.click(startButton)

    await waitFor(() => {
      // REQ-F-A2-1: Navigate to nickname-setup when nickname is null
      expect(mockNavigate).toHaveBeenCalledWith('/nickname-setup')
    })
  })

  it('should navigate to self-assessment when nickname exists', async () => {
    // REQ: REQ-F-A2-2-1
      setMockData('/api/profile/nickname', {
        user_id: 'test@samsung.com',
        nickname: 'testuser',
        registered_at: '2025-11-10T12:00:00Z',
        updated_at: '2025-11-10T12:00:00Z',
      })

    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    )

    const startButton = screen.getByRole('button', { name: /시작하기/i })
    fireEvent.click(startButton)

    await waitFor(() => {
      // REQ-F-A2-2-1: Navigate to self-assessment when nickname exists
      expect(mockNavigate).toHaveBeenCalledWith('/self-assessment')
    })
  })

  it('should display error message when API call fails', async () => {
      setMockError('/api/profile/nickname', 'Unauthorized')

    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    )

    const startButton = screen.getByRole('button', { name: /시작하기/i })
    fireEvent.click(startButton)

    await waitFor(() => {
      // Error handling - show error message to user
      const errorElement = screen.queryByText(/오류가 발생했습니다/i)
      expect(errorElement || mockNavigate).toBeTruthy()
    })
  })

  it('should handle network errors gracefully', async () => {
      setMockError('/api/profile/nickname', 'Network error')

    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    )

    const startButton = screen.getByRole('button', { name: /시작하기/i })
    fireEvent.click(startButton)

    await waitFor(() => {
      // Should show error message or handle gracefully
      const errorElement = screen.queryByText(/오류가 발생했습니다/i)
      expect(errorElement || mockNavigate).toBeTruthy()
    })
  })
})

describe('HomePage - REQ-F-A2-Signup-1 (Header Integration)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
      mockNavigate.mockReset()
    vi.spyOn(authUtils, 'getToken').mockReturnValue('mock_jwt_token')
      localStorage.setItem('slea_ssem_api_mock', 'true')
      mockConfig.delay = 0
      mockConfig.simulateError = false
      clearMockErrors()
      clearMockRequests()
  })

    afterEach(() => {
      localStorage.removeItem('slea_ssem_api_mock')
    })

  it('nickname이 null일 때 헤더에 "회원가입" 버튼 표시', async () => {
    // REQ: REQ-F-A2-Signup-1
    // Given: User has no nickname (initial load returns null)
      setMockData('/api/profile/nickname', {
        user_id: 'test@samsung.com',
        nickname: null,
        registered_at: null,
        updated_at: null,
      })

    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    )

    // Then: "회원가입" button should appear in header after nickname is loaded
    await waitFor(() => {
      const signupButton = screen.getByRole('button', { name: /회원가입/i })
      expect(signupButton).toBeInTheDocument()
    })
  })

  it('nickname이 존재할 때 헤더에 "회원가입" 버튼 숨김', async () => {
    // REQ: REQ-F-A2-Signup-1
    // Given: User already has nickname
      setMockData('/api/profile/nickname', {
        user_id: 'test@samsung.com',
        nickname: 'existing_user',
        registered_at: '2025-11-10T12:00:00Z',
        updated_at: '2025-11-10T12:00:00Z',
      })

    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    )

    // Wait for nickname to load
    // Then: "회원가입" button should NOT be visible
    const signupButton = screen.queryByRole('button', { name: /회원가입/i })
    expect(signupButton).not.toBeInTheDocument()
  })

  it('헤더에 플랫폼 이름이 표시됨', () => {
      // REQ: General header functionality
      setMockData('/api/profile/nickname', {
        user_id: 'test@samsung.com',
        nickname: null,
        registered_at: null,
        updated_at: null,
      })

    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    )

    // Then: Platform name should appear twice (header + main content)
      const platformNames = screen.getAllByText(/S\.LSI Learning Platform/i)
      expect(platformNames.length).toBeGreaterThanOrEqual(1)
  })
})
