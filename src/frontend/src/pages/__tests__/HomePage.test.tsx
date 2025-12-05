// REQ: REQ-F-A0-Landing-2, REQ-F-A1-Home
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import HomePage from '../HomePage'
import {
  mockConfig,
  setMockData,
  setMockAuthState,
  clearMockErrors,
} from '../../lib/transport'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

const renderHomePage = () =>
  render(
    <MemoryRouter>
      <HomePage />
    </MemoryRouter>
  )

describe('HomePage - REQ-F-A0-Landing-2, REQ-F-A1-Home', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockReset()
    localStorage.setItem('slea_ssem_api_mock', 'true')
    localStorage.removeItem('slea_ssem_cached_nickname')
    localStorage.removeItem('lastSurveyId')
    localStorage.removeItem('lastSurveyLevel')
    mockConfig.delay = 0
    mockConfig.simulateError = false
    clearMockErrors()
    // Set default mock auth state (unauthenticated)
    setMockAuthState(false, null)
    // Mock auth status API response (Public API)
    setMockData('/api/auth/status', {
      authenticated: false,
      nickname: null,
      user_id: null,
    })
  })

  afterEach(() => {
    localStorage.removeItem('slea_ssem_api_mock')
    localStorage.removeItem('slea_ssem_cached_nickname')
    localStorage.removeItem('lastSurveyId')
    localStorage.removeItem('lastSurveyLevel')
  })

  // REQ-F-A0-Landing-2: HomePage is accessible to all users (no auth required)
  it('renders for unauthenticated users', () => {
    renderHomePage()

    expect(screen.getByText(/오늘 당신의 AI 역량은/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /레벨테스트 시작하기/i })).toBeInTheDocument()
  })

  it('renders for authenticated users', () => {
    setMockAuthState(true, 'testuser')
    setMockData('/api/auth/status', {
      authenticated: true,
      nickname: 'testuser',
      user_id: 'test@samsung.com',
    })

    renderHomePage()

    expect(screen.getByText(/오늘 당신의 AI 역량은/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /레벨테스트 시작하기/i })).toBeInTheDocument()
  })

  it('renders hero copy and CTA button', () => {
    renderHomePage()

    expect(screen.getByText(/오늘 당신의 AI 역량은/i)).toBeInTheDocument()
    expect(screen.getByText(/슬아샘과 함께/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /레벨테스트 시작하기/i })).toBeInTheDocument()
  })

  // REQ-F-A1-Home: HomePage delegates to ContinuePage for leveltest flow
  it('navigates to /continue?intent=leveltest when "레벨테스트 시작하기" is clicked', async () => {
    const user = userEvent.setup()
    renderHomePage()

    const startButton = screen.getByRole('button', { name: /레벨테스트 시작하기/i })
    await user.click(startButton)

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/continue?intent=leveltest')
    })
  })

  // Note: Tests for consent/nickname/survey navigation are now in ContinuePage.test.tsx
  // HomePage only delegates to ContinuePage, it doesn't handle the flow directly
})
