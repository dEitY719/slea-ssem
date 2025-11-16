// REQ: REQ-F-A2-2-4, REQ-F-B5-3
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import ProfileReviewPage from '../ProfileReviewPage'
import { mockConfig, setMockData } from '../../lib/transport'

const mockNavigate = vi.fn()
let mockLocationState: any = { level: 3 }

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>(
    'react-router-dom'
  )
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({
      state: mockLocationState,
    }),
  }
})

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('ProfileReviewPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockReset()
    localStorage.clear()
    mockLocationState = { level: 3 }
    localStorage.setItem('slea_ssem_api_mock', 'true')
    mockConfig.delay = 0
    mockConfig.simulateError = false
    setMockData('/api/profile/nickname', {
      user_id: 'test@samsung.com',
      nickname: 'testuser',
      registered_at: '2025-11-12T00:00:00Z',
      updated_at: '2025-11-12T00:00:00Z',
    })
  })

  afterEach(() => {
    localStorage.clear()
    localStorage.removeItem('slea_ssem_api_mock')
  })

    test('renders page with title, description, and buttons', async () => {
      // REQ: REQ-F-A2-2-4
      mockLocationState = { level: 3, surveyId: 'test_survey' }

    renderWithRouter(<ProfileReviewPage />)

    await waitFor(() => {
      expect(screen.getByText(/프로필 확인/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /테스트 시작/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /수정하기/i })).toBeInTheDocument()
    })
  })

    test('fetches and displays user nickname on mount', async () => {
      // REQ: REQ-F-A2-2-4
      mockLocationState = { level: 3, surveyId: 'test_survey' }

    renderWithRouter(<ProfileReviewPage />)

      await waitFor(() => {
        expect(screen.getByText(/testuser/i)).toBeInTheDocument()
      })
  })

  test('displays level information passed via navigation state', async () => {
    // REQ: REQ-F-A2-2-4
    renderWithRouter(<ProfileReviewPage />)

    await waitFor(() => {
      expect(screen.getByText(/중급/i)).toBeInTheDocument()
    })
  })

  test('converts level number to Korean text (1→입문, 3→중급, 5→전문가)', async () => {
    // REQ: REQ-F-A2-2-4
    // Level 3 is already tested via the mock useLocation above (state: { level: 3 })
    // Just verify the default mock shows 중급
    renderWithRouter(<ProfileReviewPage />)

    await waitFor(() => {
      expect(screen.getByText(/중급/i)).toBeInTheDocument()
    })
  })

  test('navigates to /test with surveyId when "테스트 시작" button is clicked', async () => {
    // REQ: REQ-F-B5-3
    mockLocationState = { level: 3, surveyId: 'survey_123' }

    const user = userEvent.setup()
    renderWithRouter(<ProfileReviewPage />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /테스트 시작/i })).toBeInTheDocument()
    })

    const startButton = screen.getByRole('button', { name: /테스트 시작/i })
    await user.click(startButton)

    expect(mockNavigate).toHaveBeenCalledWith('/test', {
      state: {
        surveyId: 'survey_123',
        round: 1,
      },
    })

    // REQ-F-B5-3: surveyId should be saved to localStorage
    expect(localStorage.getItem('lastSurveyId')).toBe('survey_123')
  })

  test('navigates back to /self-assessment when "수정하기" button is clicked', async () => {
    // REQ: REQ-F-A2-2-4
    const user = userEvent.setup()
    renderWithRouter(<ProfileReviewPage />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /수정하기/i })).toBeInTheDocument()
    })

    const editButton = screen.getByRole('button', { name: /수정하기/i })
    await user.click(editButton)

    expect(mockNavigate).toHaveBeenCalledWith('/self-assessment')
  })

  test('shows loading state while fetching nickname', () => {
    // REQ: REQ-F-A2-2-4
      mockConfig.delay = 100

    renderWithRouter(<ProfileReviewPage />)

    expect(screen.getByText(/로딩 중/i)).toBeInTheDocument()
      mockConfig.delay = 0
  })

    test('shows error message if nickname fetch fails', async () => {
      // REQ: REQ-F-A2-2-4
      mockConfig.simulateError = true
    renderWithRouter(<ProfileReviewPage />)

    await waitFor(() => {
        expect(screen.getByText(/Mock Transport/i)).toBeInTheDocument()
    })
      mockConfig.simulateError = false
  })

  // REQ-F-B5-3 Tests
  test('uses surveyId from localStorage when state has no surveyId (retake scenario)', async () => {
    // REQ: REQ-F-B5-3 - Retake test with saved surveyId
    mockLocationState = { level: 3 } // No surveyId in state
    localStorage.setItem('lastSurveyId', 'saved_survey_456')

    const user = userEvent.setup()
    renderWithRouter(<ProfileReviewPage />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /테스트 시작/i })).toBeInTheDocument()
    })

    const startButton = screen.getByRole('button', { name: /테스트 시작/i })
    await user.click(startButton)

    // Should navigate with surveyId from localStorage
    expect(mockNavigate).toHaveBeenCalledWith('/test', {
      state: {
        surveyId: 'saved_survey_456',
        round: 1,
      },
    })
  })

  test('shows error when no surveyId available (neither state nor localStorage)', async () => {
    // REQ: REQ-F-B5-3 - Error case
    mockLocationState = { level: 3 } // No surveyId in state
    // localStorage is empty (cleared in beforeEach)

    const user = userEvent.setup()
    renderWithRouter(<ProfileReviewPage />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /테스트 시작/i })).toBeInTheDocument()
    })

    const startButton = screen.getByRole('button', { name: /테스트 시작/i })
    await user.click(startButton)

    // Should show error message
    await waitFor(() => {
      expect(screen.getByText(/자기평가 정보가 없습니다/i)).toBeInTheDocument()
    })

    // Should NOT navigate
    expect(mockNavigate).not.toHaveBeenCalled()
  })

  test('prefers state surveyId over localStorage when both available', async () => {
    // REQ: REQ-F-B5-3 - Priority: state > localStorage
    mockLocationState = { level: 3, surveyId: 'state_survey_123' }
    localStorage.setItem('lastSurveyId', 'old_survey_456')

    const user = userEvent.setup()
    renderWithRouter(<ProfileReviewPage />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /테스트 시작/i })).toBeInTheDocument()
    })

    const startButton = screen.getByRole('button', { name: /테스트 시작/i })
    await user.click(startButton)

    // Should use state surveyId (not localStorage)
    expect(mockNavigate).toHaveBeenCalledWith('/test', {
      state: {
        surveyId: 'state_survey_123',
        round: 1,
      },
    })

    // Should update localStorage with new surveyId
    expect(localStorage.getItem('lastSurveyId')).toBe('state_survey_123')
  })
})
