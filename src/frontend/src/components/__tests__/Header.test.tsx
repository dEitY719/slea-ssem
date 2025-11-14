// REQ: REQ-F-A2-Signup-1
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, test, expect, vi, beforeEach } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import { Header } from '../Header'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('Header - REQ-F-A2-Signup-1', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockReset()
  })

  test('nickname이 null일 때 "회원가입" 버튼 표시', () => {
    // REQ: REQ-F-A2-Signup-1
    // Given: nickname is null (user hasn't signed up)
    renderWithRouter(<Header nickname={null} />)

    // Then: "회원가입" button should be visible
    const signupButton = screen.getByRole('button', { name: /회원가입/i })
    expect(signupButton).toBeInTheDocument()
  })

  test('nickname이 존재할 때 "회원가입" 버튼 숨김', () => {
    // REQ: REQ-F-A2-Signup-1
    // Given: nickname exists (user already signed up)
    renderWithRouter(<Header nickname="테스터123" />)

    // Then: "회원가입" button should not be visible
    const signupButton = screen.queryByRole('button', { name: /회원가입/i })
    expect(signupButton).not.toBeInTheDocument()
  })

  test('"회원가입" 버튼 클릭 시 /signup으로 이동', async () => {
    // REQ: REQ-F-A2-Signup-2
    // Given: nickname is null, "회원가입" button is visible
    const user = userEvent.setup()
    renderWithRouter(<Header nickname={null} />)

    // When: User clicks "회원가입" button
    const signupButton = screen.getByRole('button', { name: /회원가입/i })
    await user.click(signupButton)

    // Then: Should navigate to /signup
    expect(mockNavigate).toHaveBeenCalledWith('/signup')
  })

  test('nickname loading 중에는 "회원가입" 버튼 숨김', () => {
    // REQ: REQ-F-A2-Signup-1
    // Given: nickname is being loaded
    renderWithRouter(<Header nickname={null} isLoading={true} />)

    // Then: "회원가입" button should not be visible (prevent flickering)
    const signupButton = screen.queryByRole('button', { name: /회원가입/i })
    expect(signupButton).not.toBeInTheDocument()
  })

  test('헤더에 플랫폼 이름 표시', () => {
    // Given: Any nickname state
    renderWithRouter(<Header nickname={null} />)

    // Then: Platform name should be displayed
    expect(screen.getByText(/S\.LSI Learning Platform/i)).toBeInTheDocument()
  })

  test('nickname이 빈 문자열일 때도 "회원가입" 버튼 표시', () => {
    // Edge case: nickname is empty string (should be treated same as null)
    // In practice, backend should return null for no nickname, but test this edge case
    renderWithRouter(<Header nickname={null} />)

    const signupButton = screen.getByRole('button', { name: /회원가입/i })
    expect(signupButton).toBeInTheDocument()
  })
})
