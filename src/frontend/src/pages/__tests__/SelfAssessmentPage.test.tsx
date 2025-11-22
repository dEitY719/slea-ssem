// REQ: REQ-F-A2-2-2
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import SelfAssessmentPage from '../SelfAssessmentPage'
import { submitProfileSurvey } from '../../features/profile/profileSubmission'

const mockNavigate = vi.fn()
let mockLocationState: any = null

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>(
    'react-router-dom'
  )
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({ state: mockLocationState }),
  }
})

vi.mock('../../utils/auth', () => ({
  getToken: vi.fn(() => 'mock_token'),
}))

vi.mock('../../features/profile/profileSubmission', () => ({
  submitProfileSurvey: vi.fn(),
}))

const submitProfileSurveyMock = vi.mocked(submitProfileSurvey)

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('SelfAssessmentPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockReset()
    mockLocationState = null
    submitProfileSurveyMock.mockResolvedValue({
      surveyId: 'survey-123',
      level: 'intermediate',
    })
    localStorage.removeItem('slea_ssem_career_temp')
  })

  afterEach(() => {
    localStorage.removeItem('slea_ssem_career_temp')
  })

  test('renders interest grid and level selector', () => {
    renderWithRouter(<SelfAssessmentPage />)

    expect(screen.getByText(/관심분야 및 기술 수준 입력/i)).toBeInTheDocument()
    expect(screen.getByRole('group', { name: /관심분야/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/1 - 입문/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/5 - 전문가/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /완료/i })).toBeInTheDocument()
  })

  test('enables complete button only after a level is selected', async () => {
    const user = userEvent.setup()
    renderWithRouter(<SelfAssessmentPage />)

    const completeButton = screen.getByRole('button', { name: /완료/i })
    expect(completeButton).toBeDisabled()

    await user.click(screen.getByLabelText(/3 - 중급/i))
    expect(completeButton).not.toBeDisabled()
  })

  test('submits merged career data and navigates on success', async () => {
    const user = userEvent.setup()
    localStorage.setItem(
      'slea_ssem_career_temp',
      JSON.stringify({ career: 7, jobRole: 'S', duty: 'Backend Dev' })
    )

    renderWithRouter(<SelfAssessmentPage />)

    await user.click(screen.getByLabelText(/4 - 고급/i))
    await user.click(screen.getByLabelText(/Backend/i))
    await user.click(screen.getByRole('button', { name: /완료/i }))

    await waitFor(() => {
      expect(submitProfileSurveyMock).toHaveBeenCalledWith({
        level: 4,
        career: 7,
        jobRole: 'S',
        duty: 'Backend Dev',
        interests: 'Backend',
      })
      expect(localStorage.getItem('slea_ssem_career_temp')).toBeNull()
      expect(mockNavigate).toHaveBeenCalledWith(
        '/profile-review',
        expect.objectContaining({
          replace: true,
          state: { level: 4, surveyId: 'survey-123' },
        })
      )
    })
  })

  test('shows error message and re-enables button when submission fails', async () => {
    const user = userEvent.setup()
    submitProfileSurveyMock.mockRejectedValueOnce(new Error('API error'))

    renderWithRouter(<SelfAssessmentPage />)
    await user.click(screen.getByLabelText(/2 - 초급/i))

    const completeButton = screen.getByRole('button', { name: /완료/i })
    await user.click(completeButton)

    await waitFor(() => {
      expect(screen.getByText(/API error/i)).toBeInTheDocument()
      expect(completeButton).not.toBeDisabled()
      expect(mockNavigate).not.toHaveBeenCalled()
    })
  })

  test('pre-fills level and interests in retake mode', () => {
    mockLocationState = {
      retakeMode: true,
      profileData: {
        level: 'inter-advanced',
        interests: ['AI'],
      },
    }

    renderWithRouter(<SelfAssessmentPage />)

    expect(
      (screen.getByLabelText(/3 - 중급/i) as HTMLInputElement).checked
    ).toBe(true)
  })
})
