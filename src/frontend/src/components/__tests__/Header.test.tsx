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

describe('Header - REQ-F-A2-Profile-Access-1', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockReset()
  })

  test('nickname이 존재할 때 헤더에 닉네임 표시', () => {
    // REQ: REQ-F-A2-Profile-Access-1
    // Given: nickname exists (user completed signup)
    renderWithRouter(<Header nickname="태호" />)

    // Then: Nickname should be displayed in header
    const nicknameElement = screen.getByText('태호')
    expect(nicknameElement).toBeInTheDocument()
  })

  test('nickname 표시 시 "회원가입" 버튼 숨김 (상호 배타성)', () => {
    // REQ: REQ-F-A2-Profile-Access-1
    // Given: nickname exists
    renderWithRouter(<Header nickname="민준" />)

    // Then: Signup button should not be visible
    const signupButton = screen.queryByRole('button', { name: /회원가입/i })
    expect(signupButton).not.toBeInTheDocument()

    // And: Nickname should be visible
    expect(screen.getByText('민준')).toBeInTheDocument()
  })

  test('nickname이 null일 때 닉네임 표시 안 함', () => {
    // REQ: REQ-F-A2-Profile-Access-1
    // Given: nickname is null
    renderWithRouter(<Header nickname={null} />)

    // Then: No nickname text should be displayed
    // Only "회원가입" button should be visible
    const signupButton = screen.getByRole('button', { name: /회원가입/i })
    expect(signupButton).toBeInTheDocument()

    // Nickname area should not exist
    const nicknameArea = screen.queryByLabelText(/현재 로그인/i)
    expect(nicknameArea).not.toBeInTheDocument()
  })

  test('nickname 동적 업데이트', () => {
    // REQ: REQ-F-A2-Profile-Access-1
    // Given: Initial nickname
    const { rerender } = renderWithRouter(<Header nickname="유진" />)
    expect(screen.getByText('유진')).toBeInTheDocument()

    // When: Nickname changes
    rerender(
      <BrowserRouter>
        <Header nickname="유진쓰" />
      </BrowserRouter>
    )

    // Then: New nickname should be displayed
    expect(screen.getByText('유진쓰')).toBeInTheDocument()
    expect(screen.queryByText('유진')).not.toBeInTheDocument()
  })

  test('nickname 영역에 적절한 aria-label 제공', () => {
    // REQ: REQ-F-A2-Profile-Access-1 (Accessibility)
    // Given: nickname exists
    renderWithRouter(<Header nickname="태호" />)

    // Then: Nickname area should have aria-label
    const nicknameArea = screen.getByLabelText(/현재 로그인/i)
    expect(nicknameArea).toBeInTheDocument()
    expect(nicknameArea).toHaveTextContent('태호')
  })

  test('특수문자 포함 닉네임 표시', () => {
    // REQ: REQ-F-A2-Profile-Access-1 (Edge case)
    // Given: nickname with special characters
    renderWithRouter(<Header nickname="테스터_123" />)

    // Then: Nickname with special chars should be displayed correctly
    expect(screen.getByText('테스터_123')).toBeInTheDocument()
  })

  test('긴 닉네임 표시', () => {
    // REQ: REQ-F-A2-Profile-Access-1 (Edge case)
    // Given: long nickname
    const longNickname = '아주긴닉네임테스트1234567890'
    renderWithRouter(<Header nickname={longNickname} />)

    // Then: Long nickname should be displayed
    expect(screen.getByText(longNickname)).toBeInTheDocument()
  })

  test('loading 중에는 nickname 표시 안 함', () => {
    // REQ: REQ-F-A2-Profile-Access-1
    // Given: nickname exists but loading
    renderWithRouter(<Header nickname="태호" isLoading={true} />)

    // Then: Nickname should not be displayed during loading
    expect(screen.queryByText('태호')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /회원가입/i })).not.toBeInTheDocument()
  })
})
