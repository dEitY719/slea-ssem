// REQ: REQ-F-A2-2
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, test, expect, vi, beforeEach } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import NicknameSetupPage from '../NicknameSetupPage'
import * as transport from '../../lib/transport'

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

// Mock transport
vi.mock('../../lib/transport', () => ({
  transport: {
    post: vi.fn(),
  },
}))

// Mock auth utils
vi.mock('../../utils/auth', () => ({
  getToken: vi.fn(() => 'mock_token'),
}))

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('NicknameSetupPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockReset()
  })

  test('renders nickname input field, check button, and next button', () => {
    // REQ: REQ-F-A2-2
    renderWithRouter(<NicknameSetupPage />)

    expect(screen.getByLabelText(/닉네임/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /중복 확인/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /다음/i })).toBeInTheDocument()
  })

  test('keeps next button disabled initially', () => {
    // REQ: REQ-F-A2-6
    renderWithRouter(<NicknameSetupPage />)

    const nextButton = screen.getByRole('button', { name: /다음/i })
    expect(nextButton).toBeDisabled()
  })

  test('shows available message when nickname is not taken', async () => {
    // REQ: REQ-F-A2-2
    const mockResponse = { available: true, suggestions: [] }
    vi.mocked(transport.transport.post).mockResolvedValueOnce(mockResponse)

    const user = userEvent.setup()
    renderWithRouter(<NicknameSetupPage />)

    const input = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })

    await user.type(input, 'john_doe')
    await user.click(checkButton)

    await waitFor(() => {
      expect(screen.getByText(/사용 가능한 닉네임입니다/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /다음/i })).not.toBeDisabled()
    })
  })

  test('re-disables next button when nickname changes after success', async () => {
    // REQ: REQ-F-A2-6
    const mockResponse = { available: true, suggestions: [] }
    vi.mocked(transport.transport.post).mockResolvedValueOnce(mockResponse)

    const user = userEvent.setup()
    renderWithRouter(<NicknameSetupPage />)

    const input = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })
    const nextButton = screen.getByRole('button', { name: /다음/i })

    await user.type(input, 'john_doe')
    await user.click(checkButton)

    await waitFor(() => {
      expect(nextButton).not.toBeDisabled()
    })

    await user.type(input, 'x')

    expect(nextButton).toBeDisabled()
    expect(screen.queryByText(/사용 가능한 닉네임입니다/i)).not.toBeInTheDocument()
  })

  test('shows taken message when nickname is already used', async () => {
    // REQ: REQ-F-A2-2
    const mockResponse = {
      available: false,
      suggestions: ['john_doe1', 'john_doe2', 'john_doe3'],
    }
    vi.mocked(transport.transport.post).mockResolvedValueOnce(mockResponse)

    const user = userEvent.setup()
    renderWithRouter(<NicknameSetupPage />)

    const input = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })

    await user.type(input, 'existing_user')
    await user.click(checkButton)

    await waitFor(() => {
      expect(screen.getByText(/이미 사용 중인 닉네임입니다/i)).toBeInTheDocument()
    })
  })

  test('shows error for nickname shorter than 3 characters', async () => {
    // REQ: REQ-F-A2-2 (validation)
    const user = userEvent.setup()
    renderWithRouter(<NicknameSetupPage />)

    const input = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })

    await user.type(input, 'ab')
    await user.click(checkButton)

    // Validation error is synchronous, no need to wait
    expect(screen.getByText(/3자 이상/i)).toBeInTheDocument()
  })

  test('shows error for invalid characters in nickname', async () => {
    // REQ: REQ-F-A2-2 (validation)
    const user = userEvent.setup()
    renderWithRouter(<NicknameSetupPage />)

    const input = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })

    await user.type(input, 'john@doe')
    await user.click(checkButton)

    // Validation error is synchronous, no need to wait
    expect(
      screen.getByText('닉네임은 영문자, 숫자, 언더스코어만 사용 가능합니다.')
    ).toBeInTheDocument()
  })

  test('disables check button while checking', async () => {
    // REQ: REQ-F-A2-2
    const mockResponse = { available: true, suggestions: [] }
    vi.mocked(transport.transport.post).mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          setTimeout(() => resolve(mockResponse), 100)
        })
    )

    const user = userEvent.setup()
    renderWithRouter(<NicknameSetupPage />)

    const input = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })
    const nextButton = screen.getByRole('button', { name: /다음/i })

    await user.type(input, 'john_doe')
    await user.click(checkButton)

    // Button should be disabled while checking
    expect(checkButton).toBeDisabled()
    expect(nextButton).toBeDisabled()

    await waitFor(() => {
      expect(checkButton).not.toBeDisabled()
      expect(nextButton).not.toBeDisabled()
    })
  })

  test('submits nickname and navigates to self assessment after success', async () => {
    // REQ: REQ-F-A2-7
    const mockPost = vi.mocked(transport.transport.post)
    mockPost.mockResolvedValueOnce({ available: true, suggestions: [] })
    mockPost.mockResolvedValueOnce({
      success: true,
      message: '닉네임 등록 완료',
      user_id: 'mock_user',
      nickname: 'john_doe',
      registered_at: '2025-11-11T00:00:00Z',
    })

    const user = userEvent.setup()
    renderWithRouter(<NicknameSetupPage />)

    const input = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })
    const nextButton = screen.getByRole('button', { name: /다음/i })

    await user.type(input, 'john_doe')
    await user.click(checkButton)

    await waitFor(() => {
      expect(screen.getByText(/사용 가능한 닉네임입니다/i)).toBeInTheDocument()
      expect(nextButton).not.toBeDisabled()
    })

    await user.click(nextButton)

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith('/profile/register', { nickname: 'john_doe' })
      expect(mockNavigate).toHaveBeenCalledWith('/self-assessment', { replace: true })
    })
  })

  test('shows error message when nickname registration fails', async () => {
    // REQ: REQ-F-A2-7
    const mockPost = vi.mocked(transport.transport.post)
    mockPost.mockResolvedValueOnce({ available: true, suggestions: [] })
    mockPost.mockRejectedValueOnce(new Error('Server error'))

    const user = userEvent.setup()
    renderWithRouter(<NicknameSetupPage />)

    const input = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })
    const nextButton = screen.getByRole('button', { name: /다음/i })

    await user.type(input, 'john_doe')
    await user.click(checkButton)

    await waitFor(() => {
      expect(screen.getByText(/사용 가능한 닉네임입니다/i)).toBeInTheDocument()
      expect(nextButton).not.toBeDisabled()
    })

    await user.click(nextButton)

    await waitFor(() => {
      expect(screen.getByText(/Server error/i)).toBeInTheDocument()
      expect(nextButton).toBeDisabled()
      expect(mockNavigate).not.toHaveBeenCalled()
    })
  })
})
