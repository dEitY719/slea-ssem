// REQ: REQ-F-A2-Signup-3, REQ-F-A2-Signup-4
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, test, expect, vi, beforeEach } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import SignupPage from '../SignupPage'
import * as transport from '../../lib/transport'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// Mock transport
vi.mock('../../lib/transport', () => ({
  transport: {
    post: vi.fn(),
    get: vi.fn(),
  },
}))

// Mock auth utils
vi.mock('../../utils/auth', () => ({
  getToken: vi.fn(() => 'mock_token'),
}))

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('SignupPage - REQ-F-A2-Signup-3 (Nickname Section)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockReset()
  })

  // Test 1: Basic rendering
  test('renders nickname section with input field and check button', () => {
    // REQ: REQ-F-A2-Signup-3 - 닉네임 입력 필드 + "중복 확인" 버튼
    renderWithRouter(<SignupPage />)

    // Check page title
    expect(screen.getByRole('heading', { name: /회원가입/i })).toBeInTheDocument()

    // Check nickname section exists
    expect(screen.getByLabelText(/닉네임/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /중복 확인/i })).toBeInTheDocument()
    expect(
      screen.getByPlaceholderText(/영문자, 숫자, 언더스코어 \(3-30자\)/i)
    ).toBeInTheDocument()
  })

  // Test 2: Input validation - too short
  test('shows error message when nickname is less than 3 characters', async () => {
    // REQ: REQ-F-A2-Signup-3 - 실시간 유효성 검사
    const user = userEvent.setup()
    renderWithRouter(<SignupPage />)

    const input = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })

    await user.type(input, 'ab')
    await user.click(checkButton)

    await waitFor(() => {
      expect(screen.getByText(/닉네임은 3자 이상이어야 합니다/i)).toBeInTheDocument()
    })
  })

  // Test 3: Input field respects maxLength attribute
  test('input field prevents typing more than 30 characters', async () => {
    // REQ: REQ-F-A2-Signup-3 - 30자 제한 (HTML maxLength)
    const user = userEvent.setup()
    renderWithRouter(<SignupPage />)

    const input = screen.getByLabelText(/닉네임/i) as HTMLInputElement

    // Try to type 35 characters
    await user.type(input, 'a'.repeat(35))

    // Verify input value is capped at 30 characters
    expect(input.value).toHaveLength(30)
    expect(input.value).toBe('a'.repeat(30))
  })

  // Test 4: Input validation - invalid characters
  test('shows error message when nickname contains invalid characters', async () => {
    // REQ: REQ-F-A2-Signup-3 - 실시간 유효성 검사
    const user = userEvent.setup()
    renderWithRouter(<SignupPage />)

    const input = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })

    await user.type(input, 'john-doe!')
    await user.click(checkButton)

    await waitFor(() => {
      expect(
        screen.getByText(/영문자, 숫자, 언더스코어만 사용 가능합니다/i)
      ).toBeInTheDocument()
    })
  })

  // Test 5: Successful nickname check (available)
  test('shows success message when nickname is available', async () => {
    // REQ: REQ-F-A2-Signup-3 - 중복 확인 정상 작동
    const mockResponse = { available: true, suggestions: [] }
    vi.mocked(transport.transport.post).mockResolvedValueOnce(mockResponse)

    const user = userEvent.setup()
    renderWithRouter(<SignupPage />)

    const input = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })

    await user.type(input, 'john_doe')
    await user.click(checkButton)

    await waitFor(() => {
      expect(screen.getByText(/사용 가능한 닉네임입니다/i)).toBeInTheDocument()
    })

    // Verify API was called with correct data
    expect(transport.transport.post).toHaveBeenCalledWith(
      '/api/profile/nickname/check',
      { nickname: 'john_doe' }
    )
  })

  // Test 6: Nickname taken - shows suggestions
  test('shows error message and suggestions when nickname is taken', async () => {
    // REQ: REQ-F-A2-Signup-3 - 중복 시 대안 3개 제안
    const mockResponse = {
      available: false,
      suggestions: ['john_doe_1', 'john_doe_2', 'john_doe_3'],
    }
    vi.mocked(transport.transport.post).mockResolvedValueOnce(mockResponse)

    const user = userEvent.setup()
    renderWithRouter(<SignupPage />)

    const input = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })

    await user.type(input, 'john_doe')
    await user.click(checkButton)

    await waitFor(() => {
      expect(screen.getByText(/이미 사용 중인 닉네임입니다/i)).toBeInTheDocument()
    })

    // Check that all 3 suggestions are displayed
    expect(screen.getByText('john_doe_1')).toBeInTheDocument()
    expect(screen.getByText('john_doe_2')).toBeInTheDocument()
    expect(screen.getByText('john_doe_3')).toBeInTheDocument()
  })

  // Test 7: Clicking suggestion auto-fills input
  test('clicking a suggestion auto-fills the nickname input', async () => {
    // REQ: REQ-F-A2-Signup-3 - 대안 클릭 시 자동 입력
    const mockResponse = {
      available: false,
      suggestions: ['john_doe_1', 'john_doe_2', 'john_doe_3'],
    }
    vi.mocked(transport.transport.post).mockResolvedValueOnce(mockResponse)

    const user = userEvent.setup()
    renderWithRouter(<SignupPage />)

    const input = screen.getByLabelText(/닉네임/i) as HTMLInputElement
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })

    await user.type(input, 'john_doe')
    await user.click(checkButton)

    await waitFor(() => {
      expect(screen.getByText('john_doe_1')).toBeInTheDocument()
    })

    // Click first suggestion
    const suggestionButton = screen.getByText('john_doe_1')
    await user.click(suggestionButton)

    // Verify input value changed
    expect(input.value).toBe('john_doe_1')

    // Verify suggestions and error message cleared
    expect(screen.queryByText(/이미 사용 중인 닉네임입니다/i)).not.toBeInTheDocument()
  })

  // Test 8: API error handling
  test('shows error message when nickname check API fails', async () => {
    // REQ: REQ-F-A2-Signup-3 - 에러 처리
    vi.mocked(transport.transport.post).mockRejectedValueOnce(
      new Error('Network error')
    )

    const user = userEvent.setup()
    renderWithRouter(<SignupPage />)

    const input = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })

    await user.type(input, 'john_doe')
    await user.click(checkButton)

    await waitFor(() => {
      expect(screen.getByText(/Network error/i)).toBeInTheDocument()
    })
  })

  // Test 9: Check button disabled when input is empty
  test('keeps check button disabled when input is empty', () => {
    // REQ: REQ-F-A2-Signup-3 - UX: 빈 입력 시 버튼 비활성화
    renderWithRouter(<SignupPage />)

    const checkButton = screen.getByRole('button', { name: /중복 확인/i })
    expect(checkButton).toBeDisabled()
  })

  // Test 10: Check button enabled when input has value
  test('enables check button when input has value', async () => {
    // REQ: REQ-F-A2-Signup-3 - UX: 입력 시 버튼 활성화
    const user = userEvent.setup()
    renderWithRouter(<SignupPage />)

    const input = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })

    expect(checkButton).toBeDisabled()

    await user.type(input, 'abc')

    expect(checkButton).not.toBeDisabled()
  })

  // Test 11: Shows "확인 중..." while checking
  test('shows loading state while checking nickname', async () => {
    // REQ: REQ-F-A2-Signup-3 - UX: 로딩 상태 표시
    const mockResponse = { available: true, suggestions: [] }
    vi.mocked(transport.transport.post).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve(mockResponse), 100))
    )

    const user = userEvent.setup()
    renderWithRouter(<SignupPage />)

    const input = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })

    await user.type(input, 'john_doe')
    await user.click(checkButton)

    // Should show loading state
    expect(screen.getByText(/확인 중/i)).toBeInTheDocument()

    // Wait for completion
    await waitFor(() => {
      expect(screen.queryByText(/확인 중/i)).not.toBeInTheDocument()
    })
  })
})

describe('SignupPage - REQ-F-A2-Signup-4 (Level Radio Buttons)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockReset()
  })

  // Test 1: Render level options with 5 radio buttons
  test('renders level selection with 5 options', () => {
    // REQ: REQ-F-A2-Signup-4 - 수준 (1~5 라디오 버튼)
    renderWithRouter(<SignupPage />)

    // Check profile section title
    expect(screen.getByRole('heading', { name: /자기평가 정보/i })).toBeInTheDocument()

    // Check all 5 level options exist
    expect(screen.getByLabelText(/1 - 입문/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/2 - 초급/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/3 - 중급/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/4 - 고급/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/5 - 전문가/i)).toBeInTheDocument()
  })

  // Test 2: Initial state - no level selected
  test('no level is selected initially', () => {
    // REQ: REQ-F-A2-Signup-4 - 초기 상태
    renderWithRouter(<SignupPage />)

    const level1Radio = screen.getByLabelText(/1 - 입문/i) as HTMLInputElement
    const level2Radio = screen.getByLabelText(/2 - 초급/i) as HTMLInputElement
    const level3Radio = screen.getByLabelText(/3 - 중급/i) as HTMLInputElement
    const level4Radio = screen.getByLabelText(/4 - 고급/i) as HTMLInputElement
    const level5Radio = screen.getByLabelText(/5 - 전문가/i) as HTMLInputElement

    expect(level1Radio.checked).toBe(false)
    expect(level2Radio.checked).toBe(false)
    expect(level3Radio.checked).toBe(false)
    expect(level4Radio.checked).toBe(false)
    expect(level5Radio.checked).toBe(false)
  })

  // Test 3: Select level 1
  test('selects level 1 when clicked', async () => {
    // REQ: REQ-F-A2-Signup-4 - 레벨 선택
    const user = userEvent.setup()
    renderWithRouter(<SignupPage />)

    const level1Radio = screen.getByLabelText(/1 - 입문/i)
    await user.click(level1Radio)

    expect(level1Radio).toBeChecked()
  })

  // Test 4: Select level 3
  test('selects level 3 when clicked', async () => {
    // REQ: REQ-F-A2-Signup-4 - 레벨 선택
    const user = userEvent.setup()
    renderWithRouter(<SignupPage />)

    const level3Radio = screen.getByLabelText(/3 - 중급/i)
    await user.click(level3Radio)

    expect(level3Radio).toBeChecked()
  })

  // Test 5: Select level 5
  test('selects level 5 when clicked', async () => {
    // REQ: REQ-F-A2-Signup-4 - 레벨 선택
    const user = userEvent.setup()
    renderWithRouter(<SignupPage />)

    const level5Radio = screen.getByLabelText(/5 - 전문가/i)
    await user.click(level5Radio)

    expect(level5Radio).toBeChecked()
  })

  // Test 6: Only one level can be selected at a time
  test('only one level can be selected at a time', async () => {
    // REQ: REQ-F-A2-Signup-4 - 단일 선택 (라디오 버튼)
    const user = userEvent.setup()
    renderWithRouter(<SignupPage />)

    const level2Radio = screen.getByLabelText(/2 - 초급/i) as HTMLInputElement
    const level4Radio = screen.getByLabelText(/4 - 고급/i) as HTMLInputElement

    // Select level 2
    await user.click(level2Radio)
    expect(level2Radio.checked).toBe(true)
    expect(level4Radio.checked).toBe(false)

    // Select level 4 (should deselect level 2)
    await user.click(level4Radio)
    expect(level2Radio.checked).toBe(false)
    expect(level4Radio.checked).toBe(true)
  })

  // Test 7: Level descriptions are displayed
  test('displays description for each level option', () => {
    // REQ: REQ-F-A2-Signup-4 - 레벨 설명 표시
    renderWithRouter(<SignupPage />)

    expect(screen.getByText(/기초 개념 학습 중/i)).toBeInTheDocument()
    expect(screen.getByText(/기본 업무 수행 가능/i)).toBeInTheDocument()
    expect(screen.getByText(/독립적으로 업무 수행/i)).toBeInTheDocument()
    expect(screen.getByText(/복잡한 문제 해결 가능/i)).toBeInTheDocument()
    expect(screen.getByText(/다른 사람을 지도 가능/i)).toBeInTheDocument()
  })
})

describe('SignupPage - REQ-F-A2-Signup-5 (Submit Button Activation)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockReset()
  })

  // Test 1: Happy path - all conditions met
  test('enables submit button when nickname is available and level is selected', async () => {
    // REQ: REQ-F-A2-Signup-5 - 닉네임 중복 확인 완료 + level 선택 시 버튼 활성화
    const mockResponse = { available: true, suggestions: [] }
    vi.mocked(transport.transport.post).mockResolvedValueOnce(mockResponse)

    const user = userEvent.setup()
    renderWithRouter(<SignupPage />)

    // Step 1: Enter nickname and check availability
    const nicknameInput = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })

    await user.type(nicknameInput, 'john_doe')
    await user.click(checkButton)

    await waitFor(() => {
      expect(screen.getByText(/사용 가능한 닉네임입니다/i)).toBeInTheDocument()
    })

    // Step 2: Select level
    const level3Radio = screen.getByLabelText(/3 - 중급/i)
    await user.click(level3Radio)

    // Assert: Submit button should be enabled
    const submitButton = screen.getByRole('button', { name: /가입 완료/i })
    expect(submitButton).not.toBeDisabled()
  })

  // Test 2: Initial state - button disabled
  test('keeps submit button disabled on initial page load', () => {
    // REQ: REQ-F-A2-Signup-5 - 초기 상태에서 버튼 비활성화
    renderWithRouter(<SignupPage />)

    const submitButton = screen.getByRole('button', { name: /가입 완료/i })
    expect(submitButton).toBeDisabled()
  })

  // Test 3: Nickname not checked - button disabled
  test('keeps submit button disabled when level is selected but nickname not checked', async () => {
    // REQ: REQ-F-A2-Signup-5 - 닉네임 미확인 시 버튼 비활성화
    const user = userEvent.setup()
    renderWithRouter(<SignupPage />)

    // Select level without checking nickname
    const level2Radio = screen.getByLabelText(/2 - 초급/i)
    await user.click(level2Radio)

    // Assert: Submit button should still be disabled
    const submitButton = screen.getByRole('button', { name: /가입 완료/i })
    expect(submitButton).toBeDisabled()
  })

  // Test 4: Nickname taken - button disabled
  test('keeps submit button disabled when nickname is taken even if level is selected', async () => {
    // REQ: REQ-F-A2-Signup-5 - 닉네임 사용 불가 시 버튼 비활성화
    const mockResponse = {
      available: false,
      suggestions: ['john_doe_1', 'john_doe_2'],
    }
    vi.mocked(transport.transport.post).mockResolvedValueOnce(mockResponse)

    const user = userEvent.setup()
    renderWithRouter(<SignupPage />)

    // Step 1: Check nickname (taken)
    const nicknameInput = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })

    await user.type(nicknameInput, 'john_doe')
    await user.click(checkButton)

    await waitFor(() => {
      expect(screen.getByText(/이미 사용 중인 닉네임입니다/i)).toBeInTheDocument()
    })

    // Step 2: Select level
    const level4Radio = screen.getByLabelText(/4 - 고급/i)
    await user.click(level4Radio)

    // Assert: Submit button should remain disabled
    const submitButton = screen.getByRole('button', { name: /가입 완료/i })
    expect(submitButton).toBeDisabled()
  })

  // Test 5: Level not selected - button disabled
  test('keeps submit button disabled when nickname is available but level is not selected', async () => {
    // REQ: REQ-F-A2-Signup-5 - level 미선택 시 버튼 비활성화
    const mockResponse = { available: true, suggestions: [] }
    vi.mocked(transport.transport.post).mockResolvedValueOnce(mockResponse)

    const user = userEvent.setup()
    renderWithRouter(<SignupPage />)

    // Step 1: Check nickname (available)
    const nicknameInput = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })

    await user.type(nicknameInput, 'john_doe')
    await user.click(checkButton)

    await waitFor(() => {
      expect(screen.getByText(/사용 가능한 닉네임입니다/i)).toBeInTheDocument()
    })

    // Step 2: Do NOT select level

    // Assert: Submit button should remain disabled
    const submitButton = screen.getByRole('button', { name: /가입 완료/i })
    expect(submitButton).toBeDisabled()
  })

  // Test 6: Real-time reactivity
  test('updates submit button state in real-time when level selection changes', async () => {
    // REQ: REQ-F-A2-Signup-5 - 조건 변경 시 실시간 반응
    const mockResponse = { available: true, suggestions: [] }
    vi.mocked(transport.transport.post).mockResolvedValueOnce(mockResponse)

    const user = userEvent.setup()
    renderWithRouter(<SignupPage />)

    // Step 1: Check nickname (available)
    const nicknameInput = screen.getByLabelText(/닉네임/i)
    const checkButton = screen.getByRole('button', { name: /중복 확인/i })

    await user.type(nicknameInput, 'john_doe')
    await user.click(checkButton)

    await waitFor(() => {
      expect(screen.getByText(/사용 가능한 닉네임입니다/i)).toBeInTheDocument()
    })

    const submitButton = screen.getByRole('button', { name: /가입 완료/i })

    // Initially disabled (no level selected)
    expect(submitButton).toBeDisabled()

    // Step 2: Select level 3
    const level3Radio = screen.getByLabelText(/3 - 중급/i)
    await user.click(level3Radio)

    // Should be enabled now
    expect(submitButton).not.toBeDisabled()

    // Step 3: Select level 5 (change selection)
    const level5Radio = screen.getByLabelText(/5 - 전문가/i)
    await user.click(level5Radio)

    // Should still be enabled (different level selected)
    expect(submitButton).not.toBeDisabled()
  })
})
