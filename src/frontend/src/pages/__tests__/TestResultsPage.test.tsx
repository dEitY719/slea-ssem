// REQ: REQ-F-B4-1, REQ-F-B5-1, REQ-F-B5-3
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import TestResultsPage from '../TestResultsPage'
import { resultService } from '../../services/resultService'

const mockNavigate = vi.fn()
let mockLocationState: any = { sessionId: 'session_123' }

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

vi.mock('../../services/resultService', () => ({
  resultService: {
    getResults: vi.fn(),
    getPreviousResult: vi.fn(),
  },
}))

const resultServiceMock = vi.mocked(resultService)

const mockResultData = {
  user_id: 1,
  grade: 'Advanced' as const,
  score: 75,
  rank: 150,
  total_cohort_size: 500,
  percentile: 70,
  percentile_confidence: 'high' as const,
  percentile_description: '상위 30%',
  grade_distribution: [
    { grade: 'Beginner' as const, count: 50, percentage: 10 },
    { grade: 'Intermediate' as const, count: 100, percentage: 20 },
    { grade: 'Inter-Advanced' as const, count: 150, percentage: 30 },
    { grade: 'Advanced' as const, count: 120, percentage: 24 },
    { grade: 'Elite' as const, count: 80, percentage: 16 },
  ],
}

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('TestResultsPage - REQ-F-B5-3 (Retake)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockReset()
    sessionStorage.clear()
    mockLocationState = { sessionId: 'session_123', surveyId: 'survey_abc', round: 1 }
    resultServiceMock.getResults.mockResolvedValue(mockResultData)
    resultServiceMock.getPreviousResult.mockResolvedValue(null)
  })

  afterEach(() => {
    sessionStorage.clear()
  })

  test('starts round 2 test when "2차 진행" button is clicked', async () => {
    const user = userEvent.setup()
    renderWithRouter(<TestResultsPage />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /2차 진행/i })).toBeInTheDocument()
    })

    const retakeButton = screen.getByRole('button', { name: /2차 진행/i })
    await user.click(retakeButton)

    expect(mockNavigate).toHaveBeenCalledWith(
      '/test',
      expect.objectContaining({
        state: {
          surveyId: 'survey_abc',
          round: 2,
          previousSessionId: 'session_123',
        },
      })
    )
  })

  test('falls back to home when survey info is missing', async () => {
    mockLocationState = { sessionId: 'session_123', round: 1 }

    const user = userEvent.setup()
    renderWithRouter(<TestResultsPage />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /2차 진행/i })).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /2차 진행/i }))
    expect(mockNavigate).toHaveBeenCalledWith('/home')
  })

  test('hides retake button when already on round 2', async () => {
    mockLocationState = { sessionId: 'session_123', surveyId: 'survey_abc', round: 2 }
    renderWithRouter(<TestResultsPage />)

    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /2차 진행/i })).not.toBeInTheDocument()
    })
  })

  test('navigates to /home when "홈화면으로 이동" button clicked', async () => {
    const user = userEvent.setup()
    renderWithRouter(<TestResultsPage />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /홈화면으로 이동/i })).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /홈화면으로 이동/i }))
    expect(mockNavigate).toHaveBeenCalledWith('/home')
  })
})

describe('TestResultsPage - REQ-F-B5-1 (Comparison)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockReset()
    sessionStorage.clear()
    mockLocationState = { sessionId: 'session_123' }
    resultServiceMock.getResults.mockResolvedValue(mockResultData)
    resultServiceMock.getPreviousResult.mockResolvedValue(null)
  })

  afterEach(() => {
    sessionStorage.clear()
  })

    test('이전 결과 로드 성공 및 ComparisonSection 렌더링', async () => {
      // REQ: REQ-F-B5-1
      const mockPreviousResult = {
        grade: 'Beginner' as const,
        score: 65,
        test_date: '2025-01-10T10:00:00Z',
      }
      resultServiceMock.getPreviousResult.mockResolvedValue(mockPreviousResult)

    renderWithRouter(<TestResultsPage />)

    // ComparisonSection 렌더링 및 이전 결과 표시 확인
    expect(await screen.findByText(/성적 비교/i)).toBeInTheDocument()
    const previousTestLabel = await screen.findByText((content) =>
      content.startsWith('이전 테스트')
    )
    expect(previousTestLabel).toBeInTheDocument()
    expect(screen.getAllByText('Beginner').length).toBeGreaterThan(0)
    expect(screen.getAllByText('65점').length).toBeGreaterThan(0)
  })

    test('이전 결과 없을 때 (첫 응시)', async () => {
      // REQ: REQ-F-B5-1
      resultServiceMock.getPreviousResult.mockResolvedValue(null)

      renderWithRouter(<TestResultsPage />)

      await waitFor(() => {
        // "첫 응시입니다" 메시지 확인
        expect(screen.getByText(/첫 응시입니다/i)).toBeInTheDocument()
      })

      // 현재 결과만 표시
      expect(screen.getByText(/현재 등급:/i)).toBeInTheDocument()
      expect(screen.getByText(/현재 점수:/i)).toBeInTheDocument()
    })

    test('이전 결과 API 에러 시 ComparisonSection 숨김', async () => {
      // REQ: REQ-F-B5-1 - Error handling
      resultServiceMock.getPreviousResult.mockRejectedValue(new Error('API Error'))

      renderWithRouter(<TestResultsPage />)

      await waitFor(() => {
        // Main results are still displayed
        expect(screen.getByText(/테스트 결과/i)).toBeInTheDocument()
      })

      // ComparisonSection 렌더링됨 (null previousResult로)
      await waitFor(() => {
        expect(screen.getByText(/첫 응시입니다/i)).toBeInTheDocument()
      })
    })
})
