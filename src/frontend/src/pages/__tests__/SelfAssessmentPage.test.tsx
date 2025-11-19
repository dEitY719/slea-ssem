// REQ: REQ-F-A2-2-2
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import SelfAssessmentPage from '../SelfAssessmentPage'
import { mockConfig, setMockScenario, getMockData } from '../../lib/transport'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>(
    'react-router-dom'
  )
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// Mock auth utils
vi.mock('../../utils/auth', () => ({
  getToken: vi.fn(() => 'mock_token'),
}))

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('SelfAssessmentPage', () => {
    beforeEach(() => {
      vi.clearAllMocks()
      mockNavigate.mockReset()
      localStorage.setItem('slea_ssem_api_mock', 'true')
      localStorage.removeItem('lastSurveyId')
      localStorage.removeItem('lastSurveyLevel')
      mockConfig.delay = 0
      mockConfig.simulateError = false
      setMockScenario('no-survey')
    })

    afterEach(() => {
      localStorage.removeItem('slea_ssem_api_mock')
      localStorage.removeItem('lastSurveyId')
      localStorage.removeItem('lastSurveyLevel')
    })

  test('renders all 5 input fields with correct types', () => {
    // REQ: REQ-F-A2-2-2 - 5개 필드 레이아웃
    renderWithRouter(<SelfAssessmentPage />)

    expect(screen.getByText(/자기평가 입력/i)).toBeInTheDocument()

    // 1. 수준 (슬라이더 1-5)
    expect(screen.getByLabelText(/1 - 입문/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/2 - 초급/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/3 - 중급/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/4 - 고급/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/5 - 전문가/i)).toBeInTheDocument()

    // 2. 경력(연차) - 숫자 입력
    expect(screen.getByLabelText(/경력/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/경력/i)).toHaveAttribute('type', 'number')

    // 3. 직군 - 라디오버튼 (S, E, M, G, F)
    expect(screen.getByLabelText('S')).toBeInTheDocument()
    expect(screen.getByLabelText('E')).toBeInTheDocument()
    expect(screen.getByLabelText('M')).toBeInTheDocument()
    expect(screen.getByLabelText('G')).toBeInTheDocument()
    expect(screen.getByLabelText('F')).toBeInTheDocument()

    // 4. 담당 업무 - 텍스트 입력
    expect(screen.getByLabelText(/담당 업무/i)).toBeInTheDocument()

    // 5. 관심분야 - 라디오버튼 (AI, ML, Backend, Frontend)
    expect(screen.getByLabelText(/^AI$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^ML$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Backend/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Frontend/i)).toBeInTheDocument()

    expect(screen.getByRole('button', { name: /완료/i })).toBeInTheDocument()
  })

  test('keeps complete button disabled when no level is selected', () => {
    // REQ: REQ-F-A2-2-3
    renderWithRouter(<SelfAssessmentPage />)

    const completeButton = screen.getByRole('button', { name: /완료/i })
    expect(completeButton).toBeDisabled()
  })

  test('enables complete button after selecting a level', async () => {
    // REQ: REQ-F-A2-2-3
    const user = userEvent.setup()
    renderWithRouter(<SelfAssessmentPage />)

    const level3Radio = screen.getByLabelText(/3 - 중급/i)
    await user.click(level3Radio)

    const completeButton = screen.getByRole('button', { name: /완료/i })
    expect(completeButton).not.toBeDisabled()
  })

    test('converts level 1 to "beginner" when submitting', async () => {
      // REQ: REQ-F-A2-2-2 - Uses shared LEVEL_MAPPING from profileLevels.ts
    const user = userEvent.setup()
    renderWithRouter(<SelfAssessmentPage />)

    const level1Radio = screen.getByLabelText(/1 - 입문/i)
    await user.click(level1Radio)

    const completeButton = screen.getByRole('button', { name: /완료/i })
    await user.click(completeButton)

      await waitFor(() => {
        const surveyData = getMockData('/api/profile/survey')
        expect(surveyData.level).toBe('beginner')
        expect(surveyData.career).toBe(0)
      })
  })

  test('converts level 2 and 3 to "intermediate" when submitting', async () => {
    // REQ: REQ-F-A2-2-2 - Uses shared LEVEL_MAPPING from profileLevels.ts
    const user = userEvent.setup()

    // Test level 2 -> intermediate
    const { unmount } = renderWithRouter(<SelfAssessmentPage />)
    let level2Radio = screen.getByLabelText(/2 - 초급/i)
    await user.click(level2Radio)
    let completeButton = screen.getByRole('button', { name: /완료/i })
    await user.click(completeButton)

      await waitFor(() => {
        const surveyData = getMockData('/api/profile/survey')
        expect(surveyData.level).toBe('intermediate')
      })

    // Reset and test level 3 -> intermediate
    unmount()
      setMockScenario('no-survey')
    renderWithRouter(<SelfAssessmentPage />)
    const level3Radio = screen.getByLabelText(/3 - 중급/i)
    await user.click(level3Radio)
    completeButton = screen.getByRole('button', { name: /완료/i })
    await user.click(completeButton)

      await waitFor(() => {
        const surveyData = getMockData('/api/profile/survey')
        expect(surveyData.level).toBe('intermediate')
      })
  })

  test('converts level 4 and 5 to "advanced" when submitting', async () => {
    // REQ: REQ-F-A2-2-2 - Uses shared LEVEL_MAPPING from profileLevels.ts
    const user = userEvent.setup()

    // Test level 4 -> advanced
    const { unmount } = renderWithRouter(<SelfAssessmentPage />)
    let level4Radio = screen.getByLabelText(/4 - 고급/i)
    await user.click(level4Radio)
    let completeButton = screen.getByRole('button', { name: /완료/i })
    await user.click(completeButton)

      await waitFor(() => {
        const surveyData = getMockData('/api/profile/survey')
        expect(surveyData.level).toBe('advanced')
      })

    // Reset and test level 5 -> advanced
    unmount()
      setMockScenario('no-survey')
    renderWithRouter(<SelfAssessmentPage />)
    const level5Radio = screen.getByLabelText(/5 - 전문가/i)
    await user.click(level5Radio)
    completeButton = screen.getByRole('button', { name: /완료/i })
    await user.click(completeButton)

      await waitFor(() => {
        const surveyData = getMockData('/api/profile/survey')
        expect(surveyData.level).toBe('advanced')
      })
  })

  test('navigates to profile review page after successful submission', async () => {
    // REQ: REQ-F-A2-2-4
    const user = userEvent.setup()
    renderWithRouter(<SelfAssessmentPage />)

    const level3Radio = screen.getByLabelText(/3 - 중급/i)
    await user.click(level3Radio)

    const completeButton = screen.getByRole('button', { name: /완료/i })
    await user.click(completeButton)

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith(
          '/profile-review',
          expect.objectContaining({
            replace: true,
            state: expect.objectContaining({
              level: 3,
              surveyId: expect.any(String),
            }),
          })
        )
      })
  })

  test('shows error message when API call fails', async () => {
    // REQ: REQ-F-A2-2-4
    const user = userEvent.setup()
    renderWithRouter(<SelfAssessmentPage />)

    const level3Radio = screen.getByLabelText(/3 - 중급/i)
    await user.click(level3Radio)

      const completeButton = screen.getByRole('button', { name: /완료/i })
      mockConfig.simulateError = true
    await user.click(completeButton)

    await waitFor(() => {
        expect(screen.getByText(/Mock Transport/i)).toBeInTheDocument()
      expect(mockNavigate).not.toHaveBeenCalled()
    })
      mockConfig.simulateError = false
  })

  test('shows description for each level (1-5)', () => {
    // REQ: REQ-F-A2-2-2
    renderWithRouter(<SelfAssessmentPage />)

    expect(screen.getByText(/기초 개념 학습 중/i)).toBeInTheDocument()
    expect(screen.getByText(/기본 업무 수행 가능/i)).toBeInTheDocument()
    expect(screen.getByText(/독립적으로 업무 수행/i)).toBeInTheDocument()
    expect(screen.getByText(/복잡한 문제 해결 가능/i)).toBeInTheDocument()
    expect(screen.getByText(/다른 사람을 지도 가능/i)).toBeInTheDocument()
  })

    test('disables complete button while submitting', async () => {
      // REQ: REQ-F-A2-2-4
    const user = userEvent.setup()
    renderWithRouter(<SelfAssessmentPage />)

    const level3Radio = screen.getByLabelText(/3 - 중급/i)
    await user.click(level3Radio)

    const completeButton = screen.getByRole('button', { name: /완료/i })
      mockConfig.delay = 100
      await user.click(completeButton)

    // Button should be disabled while submitting
    expect(completeButton).toBeDisabled()
    expect(screen.getByText(/제출 중.../i)).toBeInTheDocument()

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith(
          '/profile-review',
          expect.objectContaining({
            replace: true,
            state: expect.objectContaining({
              level: 3,
              surveyId: expect.any(String),
            }),
          })
        )
      })
      mockConfig.delay = 0
  })

  test('submits all fields with correct backend API transformation', async () => {
    // REQ: REQ-F-A2-2-2 - 백엔드 API 변환 (level 문자열, interests 배열)
    const user = userEvent.setup()
    renderWithRouter(<SelfAssessmentPage />)

    // Fill all fields
    await user.click(screen.getByLabelText(/4 - 고급/i))
    await user.type(screen.getByLabelText(/경력/i), '10')
    await user.click(screen.getByLabelText('E'))
    await user.type(screen.getByLabelText(/담당 업무/i), 'System Architecture')
    await user.click(screen.getByLabelText(/Backend/i))

    const completeButton = screen.getByRole('button', { name: /완료/i })
    await user.click(completeButton)

    await waitFor(() => {
      const surveyData = getMockData('/api/profile/survey')
      // Level: 4 → "Advanced"
      expect(surveyData.level).toBe('advanced')
      // Career: number
      expect(surveyData.career).toBe(10)
      // Job role: "E"
      expect(surveyData.job_role).toBe('E')
      // Duty: string
      expect(surveyData.duty).toBe('System Architecture')
      // Interests: "Backend" → ["Backend"]
      expect(surveyData.interests).toEqual(['Backend'])
    })
  })

  test('validates career input range (0-50)', async () => {
    // REQ: REQ-F-A2-2-3 - 유효성 검사
    const user = userEvent.setup()
    renderWithRouter(<SelfAssessmentPage />)

    const careerInput = screen.getByLabelText(/경력/i)

    // Test min/max attributes
    expect(careerInput).toHaveAttribute('min', '0')
    expect(careerInput).toHaveAttribute('max', '50')

    // Try to enter invalid value > 50
    await user.type(careerInput, '100')
    await user.click(screen.getByLabelText(/3 - 중급/i))

    const completeButton = screen.getByRole('button', { name: /완료/i })
    await user.click(completeButton)

    // Should show validation error
    await waitFor(() => {
      expect(screen.getByText(/경력은 0~50 사이/i)).toBeInTheDocument()
    })
  })

  test('validates duty input max length (500 chars)', async () => {
    // REQ: REQ-F-A2-2-3 - 유효성 검사
    const user = userEvent.setup()
    renderWithRouter(<SelfAssessmentPage />)

    const dutyInput = screen.getByLabelText(/담당 업무/i)

    // Test maxLength attribute
    expect(dutyInput).toHaveAttribute('maxLength', '500')

    // Type exactly 500 characters - should work
    const validText = 'a'.repeat(500)
    await user.type(dutyInput, validText)

    expect(dutyInput).toHaveValue(validText)
  })

  test('allows submission with only level selected (all other fields optional)', async () => {
    // REQ: REQ-F-A2-2-2 - 모든 필드 선택사항
    const user = userEvent.setup()
    renderWithRouter(<SelfAssessmentPage />)

    // Only select level
    await user.click(screen.getByLabelText(/3 - 중급/i))

    const completeButton = screen.getByRole('button', { name: /완료/i })
    expect(completeButton).not.toBeDisabled()

    await user.click(completeButton)

    await waitFor(() => {
      const surveyData = getMockData('/api/profile/survey')
      expect(surveyData.level).toBe('intermediate')
      expect(surveyData.career).toBe(0)
      expect(surveyData.job_role).toBe('')
      expect(surveyData.duty).toBe('')
      expect(surveyData.interests).toEqual([])
    })
  })

  test('converts "AI" interest to ["AI"] array', async () => {
    // REQ: REQ-F-A2-2-2 - interests 배열 변환
    const user = userEvent.setup()
    renderWithRouter(<SelfAssessmentPage />)

    await user.click(screen.getByLabelText(/3 - 중급/i))
    await user.click(screen.getByLabelText(/^AI$/i))

    const completeButton = screen.getByRole('button', { name: /완료/i })
    await user.click(completeButton)

    await waitFor(() => {
      const surveyData = getMockData('/api/profile/survey')
      expect(surveyData.interests).toEqual(['AI'])
    })
  })

  test('converts "ML" interest to ["ML"] array', async () => {
    // REQ: REQ-F-A2-2-2 - interests 배열 변환
    const user = userEvent.setup()
    renderWithRouter(<SelfAssessmentPage />)

    await user.click(screen.getByLabelText(/3 - 중급/i))
    await user.click(screen.getByLabelText(/^ML$/i))

    const completeButton = screen.getByRole('button', { name: /완료/i })
    await user.click(completeButton)

    await waitFor(() => {
      const surveyData = getMockData('/api/profile/survey')
      expect(surveyData.interests).toEqual(['ML'])
    })
  })

  test('converts "Backend" interest to ["Backend"] array', async () => {
    // REQ: REQ-F-A2-2-2 - interests 배열 변환
    const user = userEvent.setup()
    renderWithRouter(<SelfAssessmentPage />)

    await user.click(screen.getByLabelText(/3 - 중급/i))
    await user.click(screen.getByLabelText(/Backend/i))

    const completeButton = screen.getByRole('button', { name: /완료/i })
    await user.click(completeButton)

    await waitFor(() => {
      const surveyData = getMockData('/api/profile/survey')
      expect(surveyData.interests).toEqual(['Backend'])
    })
  })
})
