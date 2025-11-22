// REQ: REQ-F-A2-1, REQ-F-A1-Home
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
} from '../../lib/transport'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

vi.mock('../../utils/auth', () => ({
  getToken: vi.fn(() => 'mock_jwt_token'),
}))

const renderHomePage = () =>
  render(
    <MemoryRouter>
      <HomePage />
    </MemoryRouter>
  )

describe('HomePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockReset()
    vi.spyOn(authUtils, 'getToken').mockReturnValue('mock_jwt_token')
    localStorage.setItem('slea_ssem_api_mock', 'true')
    localStorage.removeItem('slea_ssem_cached_nickname')
    localStorage.removeItem('lastSurveyId')
    localStorage.removeItem('lastSurveyLevel')
    mockConfig.delay = 0
    mockConfig.simulateError = false
    clearMockErrors()
    setMockData('/api/profile/nickname', {
      user_id: 'test@samsung.com',
      nickname: null,
      registered_at: null,
      updated_at: null,
    })
    setMockData('/api/profile/consent', {
      consented: false,
      consent_at: null,
    })
  })

  afterEach(() => {
    localStorage.removeItem('slea_ssem_api_mock')
    localStorage.removeItem('slea_ssem_cached_nickname')
    localStorage.removeItem('lastSurveyId')
    localStorage.removeItem('lastSurveyLevel')
  })

  it('redirects to login when no token is available', () => {
    vi.spyOn(authUtils, 'getToken').mockReturnValue(null)
    renderHomePage()
    expect(mockNavigate).toHaveBeenCalledWith('/')
  })

  it('renders hero copy and CTA button', () => {
    renderHomePage()
    expect(screen.getByText(/오늘 당신의 AI 역량은/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /레벨테스트 시작하기/i })).toBeInTheDocument()
  })

  it('navigates to consent page when user has not consented yet', async () => {
    renderHomePage()

    fireEvent.click(screen.getByRole('button', { name: /레벨테스트 시작하기/i }))

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/consent')
    })
  })

  it('navigates to nickname setup after consent when nickname is missing', async () => {
    setMockData('/api/profile/consent', { consented: true, consent_at: '2025-11-20T00:00:00Z' })
    renderHomePage()

    fireEvent.click(screen.getByRole('button', { name: /레벨테스트 시작하기/i }))

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/nickname-setup')
    })
  })

  it('navigates to career info when nickname exists and no survey progress', async () => {
    setMockData('/api/profile/consent', { consented: true, consent_at: '2025-11-20T00:00:00Z' })
    setMockData('/api/profile/nickname', {
      user_id: 'test@samsung.com',
      nickname: 'testuser',
      registered_at: '2025-11-10T12:00:00Z',
      updated_at: '2025-11-10T12:00:00Z',
    })

    renderHomePage()
    fireEvent.click(screen.getByRole('button', { name: /레벨테스트 시작하기/i }))

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/career-info')
    })
  })

  it('navigates to profile review when survey progress exists', async () => {
    setMockData('/api/profile/consent', { consented: true, consent_at: '2025-11-20T00:00:00Z' })
    setMockData('/api/profile/nickname', {
      user_id: 'test@samsung.com',
      nickname: 'testuser',
      registered_at: '2025-11-10T12:00:00Z',
      updated_at: '2025-11-10T12:00:00Z',
    })
    localStorage.setItem('lastSurveyId', 'saved_survey_789')
    localStorage.setItem('lastSurveyLevel', '4')

    renderHomePage()
    fireEvent.click(screen.getByRole('button', { name: /레벨테스트 시작하기/i }))

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith(
        '/profile-review',
        expect.objectContaining({
          state: { surveyId: 'saved_survey_789', level: 4 },
        })
      )
    })
  })

  it('shows error message when consent check fails', async () => {
    setMockError('/api/profile/consent', 'Network error')
    renderHomePage()

    fireEvent.click(screen.getByRole('button', { name: /레벨테스트 시작하기/i }))

    await waitFor(() => {
      expect(
        screen.getByText(/프로필 정보를 불러오는데 실패했습니다/i)
      ).toBeInTheDocument()
    })
  })
})
