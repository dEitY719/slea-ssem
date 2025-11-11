// REQ: REQ-F-A2-2
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, test, expect, vi, beforeEach } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import NicknameSetupPage from '../NicknameSetupPage'
import * as transport from '../../lib/transport'

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
  })

  test('renders nickname input field and check button', () => {
    // REQ: REQ-F-A2-2
    renderWithRouter(<NicknameSetupPage />)

    expect(screen.getByLabelText(/닉네임/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /중복 확인/i })).toBeInTheDocument()
  })

  test('shows available message when nickname is not taken', async () => {
    // REQ: REQ-F-A2-2
    const mockResponse = { available: true, suggestions: [] }
    vi.mocked(transport.transport.post).mockResolvedValue(mockResponse)

    const user = userEvent.setup()
    renderWithRouter(<NicknameSetupPage />)

    const input = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })

    await user.type(input, 'john_doe')
    await user.click(checkButton)

    await waitFor(() => {
      expect(screen.getByText(/사용 가능한 닉네임입니다/i)).toBeInTheDocument()
    })
  })

  test('shows taken message when nickname is already used', async () => {
    // REQ: REQ-F-A2-2
    const mockResponse = {
      available: false,
      suggestions: ['john_doe1', 'john_doe2', 'john_doe3'],
    }
    vi.mocked(transport.transport.post).mockResolvedValue(mockResponse)

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
    expect(screen.getByText(/영문자, 숫자, 언더스코어/i)).toBeInTheDocument()
  })

  test('disables check button while checking', async () => {
    // REQ: REQ-F-A2-2
    const mockResponse = { available: true, suggestions: [] }
    vi.mocked(transport.transport.post).mockImplementation(
      () =>
        new Promise((resolve) => {
          setTimeout(() => resolve(mockResponse), 100)
        })
    )

    const user = userEvent.setup()
    renderWithRouter(<NicknameSetupPage />)

    const input = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })

    await user.type(input, 'john_doe')
    await user.click(checkButton)

    // Button should be disabled while checking
    expect(checkButton).toBeDisabled()

    await waitFor(() => {
      expect(checkButton).not.toBeDisabled()
    })
  })
})
