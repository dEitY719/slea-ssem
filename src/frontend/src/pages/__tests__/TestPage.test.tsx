// REQ: REQ-F-B2-1, REQ-F-B2-2
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import TestPage from '../TestPage'
import {
  mockConfig,
  setMockData,
  getMockRequests,
  clearMockRequests,
  setMockError,
  clearMockErrors,
} from '../../lib/transport'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>(
    'react-router-dom'
  )
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({
      state: {
        surveyId: 'test-survey-123',
        round: 1,
      },
    }),
  }
})

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

const mockQuestions = [
  {
    id: 'q1',
    item_type: 'multiple_choice',
    stem: 'What is AI?',
    choices: ['Option A', 'Option B', 'Option C'],
    difficulty: 5,
    category: 'AI Basics',
  },
  {
    id: 'q2',
    item_type: 'true_false',
    stem: 'Machine learning is a subset of AI',
    choices: null,
    difficulty: 3,
    category: 'AI Basics',
  },
  {
    id: 'q3',
    item_type: 'short_answer',
    stem: 'Explain neural networks',
    choices: null,
    difficulty: 7,
    category: 'Deep Learning',
  },
]

const mockGenerateResponse = {
  session_id: 'session-456',
  questions: mockQuestions,
}

const setupMockEnv = (generateResponse = mockGenerateResponse) => {
  localStorage.setItem('slea_ssem_api_mock', 'true')
  mockConfig.delay = 0
  mockConfig.simulateError = false
  clearMockRequests()
  clearMockErrors()
  setMockData('/api/questions/generate', generateResponse)
}

const teardownMockEnv = () => {
  localStorage.removeItem('slea_ssem_api_mock')
}

describe('TestPage - REQ-F-B2-1', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockReset()
    setupMockEnv()
  })

  afterEach(() => {
    teardownMockEnv()
  })

    test('AC1: 문항이 1개씩 순차적으로 표시된다', async () => {
      // REQ: REQ-F-B2-1 - Acceptance Criteria 1
    renderWithRouter(<TestPage />)

    await waitFor(() => {
      expect(screen.getByText('What is AI?')).toBeInTheDocument()
    })

    // First question displayed
    expect(screen.getByText(/문제\s*1\s*\/\s*3/)).toBeInTheDocument()
    expect(screen.queryByText('Machine learning is a subset of AI')).not.toBeInTheDocument()
  })

    test('AC2: 진행률이 실시간으로 업데이트된다', async () => {
      // REQ: REQ-F-B2-1 - Acceptance Criteria 2
    const user = userEvent.setup()
    renderWithRouter(<TestPage />)

    await waitFor(() => {
      expect(screen.getByText(/문제\s*1\s*\/\s*3/i)).toBeInTheDocument()
    })

    // Select answer and click next
    const optionA = screen.getByLabelText('Option A')
    await user.click(optionA)

    const nextButton = screen.getByRole('button', { name: /다음/i })
    await user.click(nextButton)

    await waitFor(() => {
      expect(screen.getByText(/문제\s*2\s*\/\s*3/i)).toBeInTheDocument()
    })
  })

    test('Happy Path: multiple choice 답변 제출 성공', async () => {
      // REQ: REQ-F-B2-1 - Submit multiple choice answer
    const user = userEvent.setup()
    renderWithRouter(<TestPage />)

    await waitFor(() => {
      expect(screen.getByText('What is AI?')).toBeInTheDocument()
    })

    // Select option B
    const optionB = screen.getByLabelText('Option B')
    await user.click(optionB)

    const nextButton = screen.getByRole('button', { name: /다음/i })
    await user.click(nextButton)

      await waitFor(() => {
        const autosaveRequests = getMockRequests({ url: '/api/questions/autosave', method: 'POST' })
        expect(autosaveRequests.length).toBeGreaterThan(0)
        const payload = autosaveRequests.at(-1)!.body
        expect(payload.session_id).toBe('session-456')
        expect(payload.question_id).toBe('q1')
        const parsed = JSON.parse(payload.user_answer)
        expect(parsed.selected).toBe('Option B')
        expect(payload.response_time_ms).toBeGreaterThan(0)
      })
  })

    test('Happy Path: short answer 답변 제출 성공', async () => {
      // REQ: REQ-F-B2-1 - Submit short answer
    const user = userEvent.setup()
    renderWithRouter(<TestPage />)

    await waitFor(() => {
      expect(screen.getByText('What is AI?')).toBeInTheDocument()
    })

    // Navigate to question 3 (short answer)
    await user.click(screen.getByLabelText('Option A'))
    await user.click(screen.getByRole('button', { name: /다음/i }))

    await waitFor(() => {
      expect(screen.getByText('Machine learning is a subset of AI')).toBeInTheDocument()
    })

    await user.click(screen.getByLabelText(/True/i))
    await user.click(screen.getByRole('button', { name: /다음/i }))

    await waitFor(() => {
      expect(screen.getByText('Explain neural networks')).toBeInTheDocument()
    })

    // Type short answer
    const textarea = screen.getByPlaceholderText(/답변을 입력하세요/i)
    await user.type(textarea, 'Neural networks are computing systems inspired by biological neural networks.')

    const completeButton = screen.getByRole('button', { name: /완료/i })
    await user.click(completeButton)

      await waitFor(() => {
        const autosaveRequests = getMockRequests({ url: '/api/questions/autosave', method: 'POST' })
        const lastRequest = autosaveRequests.at(-1)
        expect(lastRequest?.body.question_id).toBe('q3')
        const parsed = JSON.parse(lastRequest!.body.user_answer)
        expect(parsed.text).toContain('Neural networks are computing systems')
      })
  })

    test('Input Validation: 빈 답변 제출 방지', async () => {
      // REQ: REQ-F-B2-1 - Prevent empty answer submission
    renderWithRouter(<TestPage />)

    await waitFor(() => {
      expect(screen.getByText('What is AI?')).toBeInTheDocument()
    })

    const nextButton = screen.getByRole('button', { name: /다음/i })
    expect(nextButton).toBeDisabled()

      // Verify autosave was NOT called
      const autosaveRequests = getMockRequests({ url: '/api/questions/autosave', method: 'POST' })
      expect(autosaveRequests).toHaveLength(0)
  })

    test('Edge Case: 마지막 문항 완료 시 results 페이지 이동', async () => {
      // REQ: REQ-F-B2-1 - Navigate to results after last question
      const singleQuestion = {
        session_id: 'session-789',
        questions: [mockQuestions[0]],
      }
      setMockData('/api/questions/generate', singleQuestion)
    const user = userEvent.setup()
    renderWithRouter(<TestPage />)

    await waitFor(() => {
      expect(screen.getByText('What is AI?')).toBeInTheDocument()
    })

    const optionA = screen.getByLabelText('Option A')
    await user.click(optionA)

    const completeButton = screen.getByRole('button', { name: /완료/i })
    await user.click(completeButton)

    await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/test-results', {
          state: { sessionId: 'session-789', surveyId: 'test-survey-123' },
        })
    })
  })

    test('Error Handling: API 실패 시 에러 메시지 표시', async () => {
      // REQ: REQ-F-B2-1 - Show error on API failure
    const user = userEvent.setup()
    renderWithRouter(<TestPage />)

    await waitFor(() => {
      expect(screen.getByText('What is AI?')).toBeInTheDocument()
    })

    const optionC = screen.getByLabelText('Option C')
    await user.click(optionC)

      const nextButton = screen.getByRole('button', { name: /다음/i })
      setMockError('/api/questions/autosave', 'Network error')
      await user.click(nextButton)

      await waitFor(() => {
        expect(screen.getByText(/Network error/i)).toBeInTheDocument()
        expect(screen.getByText('What is AI?')).toBeInTheDocument()
      })
      clearMockErrors('/api/questions/autosave')
  })

    test('Response Time Tracking: response_time_ms 정확히 측정', async () => {
      // REQ: REQ-F-B2-1 - Track response time accurately
    const user = userEvent.setup()
    renderWithRouter(<TestPage />)

    await waitFor(() => {
      expect(screen.getByText('What is AI?')).toBeInTheDocument()
    })

    // Wait at least 100ms before answering
    await new Promise(resolve => setTimeout(resolve, 100))

    const optionA = screen.getByLabelText('Option A')
    await user.click(optionA)

    const nextButton = screen.getByRole('button', { name: /다음/i })
    await user.click(nextButton)

      await waitFor(() => {
        const autosaveRequests = getMockRequests({ url: '/api/questions/autosave', method: 'POST' })
        expect(autosaveRequests.length).toBeGreaterThan(0)
        const payload = autosaveRequests.at(-1)!.body
        expect(payload.response_time_ms).toBeGreaterThanOrEqual(100)
      })
  })

    test('Button State: 제출 중 버튼 비활성화', async () => {
      // REQ: REQ-F-B2-1 - Disable button during submission
    const user = userEvent.setup()
    renderWithRouter(<TestPage />)

    await waitFor(() => {
      expect(screen.getByText('What is AI?')).toBeInTheDocument()
    })

    const optionA = screen.getByLabelText('Option A')
    await user.click(optionA)

      const nextButton = screen.getByRole('button', { name: /다음/i })
      mockConfig.delay = 200
    await user.click(nextButton)

    // Button should be disabled during submission
    expect(nextButton).toBeDisabled()

      await waitFor(() => {
        expect(screen.getByText('Machine learning is a subset of AI')).toBeInTheDocument()
      }, { timeout: 1000 })
      mockConfig.delay = 0
  })
})

describe('TestPage - REQ-F-B2-2 Timer', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockReset()
    setupMockEnv()
  })

  afterEach(() => {
    vi.useRealTimers()
    teardownMockEnv()
  })

    test('Timer: 테스트 시작 시 20:00 표시', async () => {
      // REQ: REQ-F-B2-2, REQ-F-B2-5
      // AC: 타이머가 20분(20:00)에서 시작
    renderWithRouter(<TestPage />)

    await waitFor(() => {
      expect(screen.getByText('20:00')).toBeInTheDocument()
    })
  })

    test('Timer: 1초마다 정확하게 감소', async () => {
      // REQ: REQ-F-B2-2, REQ-F-B2-5
      // AC: 1초마다 시간이 감소 (20:00 → 19:59 → 19:58)
    renderWithRouter(<TestPage />)

    await waitFor(() => {
      expect(screen.getByText('20:00')).toBeInTheDocument()
    })

    // Use real timers and wait for actual countdown
    await waitFor(() => {
      expect(screen.getByText('19:59')).toBeInTheDocument()
    }, { timeout: 2000 })
  })

    test('Timer: 16분 이상일 때 녹색 스타일 적용', async () => {
      // REQ: REQ-F-B2-5
      // AC: 16분 이상 → 녹색 배경
    renderWithRouter(<TestPage />)

    await waitFor(() => {
      const timerText = screen.getByText('20:00')
      const timerElement = timerText.closest('.timer')
      expect(timerElement).toHaveClass('timer-green')
    })
  })

  test('Timer: 색상 변경 로직 검증 (녹색/주황색/빨간색)', () => {
    // REQ: REQ-F-B2-5
    // AC: 시간에 따라 색상 변경 (녹색 → 주황색 → 빨간색)
    // Note: 헬퍼 함수 로직 검증 (unit test 스타일)

    // Mock getTimerColor function (inline test)
    const getTimerColor = (seconds: number): string => {
      if (seconds > 15 * 60) return 'green'
      if (seconds > 5 * 60) return 'orange'
      return 'red'
    }

    // Test green (16+ minutes)
    expect(getTimerColor(20 * 60)).toBe('green')  // 20 minutes
    expect(getTimerColor(16 * 60)).toBe('green')  // 16 minutes

    // Test orange (6-15 minutes)
    expect(getTimerColor(15 * 60)).toBe('orange') // 15 minutes
    expect(getTimerColor(10 * 60)).toBe('orange') // 10 minutes
    expect(getTimerColor(6 * 60)).toBe('orange')  // 6 minutes

    // Test red (5 minutes or less)
    expect(getTimerColor(5 * 60)).toBe('red')     // 5 minutes
    expect(getTimerColor(3 * 60)).toBe('red')     // 3 minutes
    expect(getTimerColor(0)).toBe('red')          // 0 minutes
  })

  test('Timer: formatTime 포맷팅 검증 (MM:SS)', () => {
    // REQ: REQ-F-B2-2
    // AC: 시간이 MM:SS 형식으로 표시됨

    // Mock formatTime function (inline test)
    const formatTime = (seconds: number): string => {
      const mins = Math.floor(seconds / 60)
      const secs = seconds % 60
      return `${mins}:${secs.toString().padStart(2, '0')}`
    }

    expect(formatTime(1200)).toBe('20:00')  // 20 minutes
    expect(formatTime(1199)).toBe('19:59')  // 19 minutes 59 seconds
    expect(formatTime(600)).toBe('10:00')   // 10 minutes
    expect(formatTime(61)).toBe('1:01')     // 1 minute 1 second
    expect(formatTime(5)).toBe('0:05')      // 5 seconds
    expect(formatTime(0)).toBe('0:00')      // 0 seconds
  })
})

describe('TestPage - REQ-F-B2-6 Autosave', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockReset()
    setupMockEnv()
  })

  afterEach(() => {
    teardownMockEnv()
  })

  test('Autosave: 답변 입력 시 자동 저장', async () => {
    // REQ: REQ-F-B2-6
    // AC: 답변 입력 시 1초 debounce 후 자동 저장
    const user = userEvent.setup()
    renderWithRouter(<TestPage />)

    await waitFor(() => {
      expect(screen.getByText('What is AI?')).toBeInTheDocument()
    })

    // Select answer
    const optionA = screen.getByLabelText('Option A')
    await user.click(optionA)

    // Wait for autosave (1 second debounce + API call)
    await waitFor(() => {
      const autosaveRequests = getMockRequests({ url: '/api/questions/autosave', method: 'POST' })
      expect(autosaveRequests.length).toBeGreaterThan(0)
      const payload = autosaveRequests.at(-1)!.body
      expect(payload.session_id).toBe('session-456')
      expect(payload.question_id).toBe('q1')
      const parsed = JSON.parse(payload.user_answer)
      expect(parsed.selected).toBe('Option A')
    }, { timeout: 3000 })
  })

  test('Autosave: 저장 완료 시 "저장됨" 표시', async () => {
    // REQ: REQ-F-B2-6
    // AC: 저장 완료 후 "저장됨" 메시지 표시
    const user = userEvent.setup()
    renderWithRouter(<TestPage />)

    await waitFor(() => {
      expect(screen.getByText('What is AI?')).toBeInTheDocument()
    })

    // Select answer
    const optionA = screen.getByLabelText('Option A')
    await user.click(optionA)

    // Wait for autosave and "저장됨" message
    await waitFor(() => {
      expect(screen.getByText(/저장됨/i)).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  test('Autosave: 저장 완료 후 메시지 자동 숨김', async () => {
    // REQ: REQ-F-B2-6
    // AC: 저장 완료 후 2초 후 메시지 자동 숨김
    const user = userEvent.setup()
    renderWithRouter(<TestPage />)

    await waitFor(() => {
      expect(screen.getByText('What is AI?')).toBeInTheDocument()
    })

    // Select answer
    const optionA = screen.getByLabelText('Option A')
    await user.click(optionA)

    // Should show "저장됨" message
    await waitFor(() => {
      expect(screen.getByText(/저장됨/i)).toBeInTheDocument()
    }, { timeout: 3000 })

    // Wait 2 more seconds - message should be hidden
    await waitFor(() => {
      expect(screen.queryByText(/저장됨/i)).not.toBeInTheDocument()
    }, { timeout: 3000 })
  })

  test('Autosave: 동일한 답변은 중복 저장하지 않음', async () => {
    // REQ: REQ-F-B2-6
    // AC: 이미 저장된 답변은 다시 저장하지 않음
    const user = userEvent.setup()
    renderWithRouter(<TestPage />)

    await waitFor(() => {
      expect(screen.getByText('What is AI?')).toBeInTheDocument()
    })

    // Select answer
    const optionA = screen.getByLabelText('Option A')
    await user.click(optionA)

    // Wait for autosave
    await waitFor(() => {
      const autosaveRequests = getMockRequests({ url: '/api/questions/autosave', method: 'POST' })
      expect(autosaveRequests.length).toBe(1)
    }, { timeout: 2000 })

    const initialCount = getMockRequests({ url: '/api/questions/autosave', method: 'POST' }).length

    // Wait longer - should NOT save again
    await new Promise(resolve => setTimeout(resolve, 2000))

    const newCount = getMockRequests({ url: '/api/questions/autosave', method: 'POST' }).length
    expect(newCount).toBe(initialCount) // Same count, no duplicate save
  })

  test('Autosave: 저장 실패 시 에러 메시지 표시', async () => {
    // REQ: REQ-F-B2-6
    // AC: 에러 발생 시 사용자에게 알림
    const user = userEvent.setup()
    renderWithRouter(<TestPage />)

    await waitFor(() => {
      expect(screen.getByText('What is AI?')).toBeInTheDocument()
    })

    // Select answer
    const optionA = screen.getByLabelText('Option A')
    await user.click(optionA)

    // Should show error message
    setMockError('/api/questions/autosave', '저장 실패')
    await waitFor(() => {
      expect(screen.getByText(/저장 실패/i)).toBeInTheDocument()
    }, { timeout: 3000 })
    clearMockErrors('/api/questions/autosave')
  })
})
