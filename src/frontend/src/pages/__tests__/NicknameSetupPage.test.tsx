// REQ: REQ-F-A2-2
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import NicknameSetupPage from '../NicknameSetupPage'
import { mockConfig } from '../../lib/transport'

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

describe('NicknameSetupPage', () => {
    beforeEach(() => {
      vi.clearAllMocks()
      mockNavigate.mockReset()
      localStorage.setItem('slea_ssem_api_mock', 'true')
      localStorage.removeItem('slea_ssem_cached_nickname')
      mockConfig.delay = 0
      mockConfig.simulateError = false
    })

    afterEach(() => {
      localStorage.removeItem('slea_ssem_api_mock')
      localStorage.removeItem('slea_ssem_cached_nickname')
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
    const user = userEvent.setup()
    renderWithRouter(<NicknameSetupPage />)

    const input = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })

    await user.type(input, 'new_user')
    await user.click(checkButton)

    await waitFor(() => {
        expect(screen.getByText(/사용 가능한 닉네임입니다/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /다음/i })).not.toBeDisabled()
    })
  })

  test('re-disables next button when nickname changes after success', async () => {
    // REQ: REQ-F-A2-6
    const user = userEvent.setup()
    renderWithRouter(<NicknameSetupPage />)

    const input = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })
    const nextButton = screen.getByRole('button', { name: /다음/i })

    await user.type(input, 'unique_user1')
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
    const user = userEvent.setup()
    renderWithRouter(<NicknameSetupPage />)

    const input = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })

    await user.type(input, 'admin')
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
    const user = userEvent.setup()
    renderWithRouter(<NicknameSetupPage />)

    const input = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })
    const nextButton = screen.getByRole('button', { name: /다음/i })

    mockConfig.delay = 100
    await user.type(input, 'delay_check')
    await user.click(checkButton)

    // Button should be disabled while checking
    expect(checkButton).toBeDisabled()
    expect(nextButton).toBeDisabled()

    await waitFor(() => {
      expect(checkButton).not.toBeDisabled()
      expect(nextButton).not.toBeDisabled()
    })
    mockConfig.delay = 0
  })

    test('submits nickname, caches it, and navigates to self assessment after success', async () => {
    // REQ: REQ-F-A2-7
    const user = userEvent.setup()
    renderWithRouter(<NicknameSetupPage />)

    const input = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })
    const nextButton = screen.getByRole('button', { name: /다음/i })

    await user.type(input, 'signup_user1')
    await user.click(checkButton)

    await waitFor(() => {
      expect(screen.getByText(/사용 가능한 닉네임입니다/i)).toBeInTheDocument()
      expect(nextButton).not.toBeDisabled()
    })

    await user.click(nextButton)

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/self-assessment', { replace: true })
      })
      expect(localStorage.getItem('slea_ssem_cached_nickname')).toBe('signup_user1')
  })

  test('shows error message when nickname registration fails', async () => {
    // REQ: REQ-F-A2-7
    const user = userEvent.setup()
    renderWithRouter(<NicknameSetupPage />)

    const input = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })
    const nextButton = screen.getByRole('button', { name: /다음/i })

    await user.type(input, 'signup_user2')
    await user.click(checkButton)

    await waitFor(() => {
      expect(screen.getByText(/사용 가능한 닉네임입니다/i)).toBeInTheDocument()
      expect(nextButton).not.toBeDisabled()
    })

    mockConfig.simulateError = true
    await user.click(nextButton)

    await waitFor(() => {
      expect(screen.getByText(/Mock Transport/i)).toBeInTheDocument()
      expect(nextButton).toBeDisabled()
      expect(mockNavigate).not.toHaveBeenCalled()
    })
    mockConfig.simulateError = false
  })

  test('shows 3 alternative suggestions when nickname is taken', async () => {
    // REQ: REQ-F-A2-4
    const user = userEvent.setup()
    renderWithRouter(<NicknameSetupPage />)

    const input = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })

    await user.type(input, 'test')
    await user.click(checkButton)

    await waitFor(() => {
      expect(screen.getByText(/추천 닉네임/i)).toBeInTheDocument()
        expect(screen.getByText('test_1')).toBeInTheDocument()
        expect(screen.getByText('test_2')).toBeInTheDocument()
        expect(screen.getByText('test_3')).toBeInTheDocument()
    })
  })

  test('fills input field when suggestion is clicked', async () => {
    // REQ: REQ-F-A2-4
    const user = userEvent.setup()
    renderWithRouter(<NicknameSetupPage />)

    const input = screen.getByLabelText(/닉네임/i) as HTMLInputElement
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })

    await user.type(input, 'test')
    await user.click(checkButton)

      await waitFor(() => {
        expect(screen.getByText('test_1')).toBeInTheDocument()
      })

      const suggestion1 = screen.getByText('test_1')
    await user.click(suggestion1)

      expect(input.value).toBe('test_1')
    expect(screen.queryByText(/이미 사용 중인 닉네임입니다/i)).not.toBeInTheDocument()
      expect(screen.queryByText('test_2')).not.toBeInTheDocument()
  })

  test('allows re-checking after selecting a suggestion', async () => {
    // REQ: REQ-F-A2-4
    const user = userEvent.setup()
    renderWithRouter(<NicknameSetupPage />)

    const input = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })

    await user.type(input, 'test')
    await user.click(checkButton)

      await waitFor(() => {
        expect(screen.getByText('test_1')).toBeInTheDocument()
      })

      const suggestion1 = screen.getByText('test_1')
    await user.click(suggestion1)

    await user.click(checkButton)

    await waitFor(() => {
      expect(screen.getByText(/사용 가능한 닉네임입니다/i)).toBeInTheDocument()
    })
  })
})
