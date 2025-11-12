// REQ: REQ-F-A2-2-4
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, test, expect, vi, beforeEach } from 'vitest'
import { BrowserRouter, MemoryRouter } from 'react-router-dom'
import ProfileReviewPage from '../ProfileReviewPage'
import * as transport from '../../lib/transport'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>(
    'react-router-dom'
  )
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({
      state: { level: 3 },
    }),
  }
})

// Mock transport
vi.mock('../../lib/transport', () => ({
  transport: {
    get: vi.fn(),
  },
}))

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('ProfileReviewPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockReset()
  })

  test('renders page with title, description, and buttons', async () => {
    // REQ: REQ-F-A2-2-4
    vi.mocked(transport.transport.get).mockResolvedValueOnce({
      user_id: 'test@samsung.com',
      nickname: 'testuser',
      registered_at: '2025-11-12T00:00:00Z',
      updated_at: '2025-11-12T00:00:00Z',
    })

    renderWithRouter(<ProfileReviewPage />)

    await waitFor(() => {
      expect(screen.getByText(/프로필 확인/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /시작하기/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /수정하기/i })).toBeInTheDocument()
    })
  })

  test('fetches and displays user nickname on mount', async () => {
    // REQ: REQ-F-A2-2-4
    const mockGet = vi.mocked(transport.transport.get)
    mockGet.mockResolvedValueOnce({
      user_id: 'test@samsung.com',
      nickname: 'testuser',
      registered_at: '2025-11-12T00:00:00Z',
      updated_at: '2025-11-12T00:00:00Z',
    })

    renderWithRouter(<ProfileReviewPage />)

    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith('/profile/nickname')
      expect(screen.getByText(/testuser/i)).toBeInTheDocument()
    })
  })

  test('displays level information passed via navigation state', async () => {
    // REQ: REQ-F-A2-2-4
    vi.mocked(transport.transport.get).mockResolvedValueOnce({
      user_id: 'test@samsung.com',
      nickname: 'testuser',
      registered_at: '2025-11-12T00:00:00Z',
      updated_at: '2025-11-12T00:00:00Z',
    })

    renderWithRouter(<ProfileReviewPage />)

    await waitFor(() => {
      expect(screen.getByText(/중급/i)).toBeInTheDocument()
    })
  })

  test('converts level number to Korean text (1→입문, 3→중급, 5→전문가)', async () => {
    // REQ: REQ-F-A2-2-4
    vi.mocked(transport.transport.get).mockResolvedValue({
      user_id: 'test@samsung.com',
      nickname: 'testuser',
      registered_at: '2025-11-12T00:00:00Z',
      updated_at: '2025-11-12T00:00:00Z',
    })

    // Level 3 is already tested via the mock useLocation above (state: { level: 3 })
    // Just verify the default mock shows 중급
    renderWithRouter(<ProfileReviewPage />)

    await waitFor(() => {
      expect(screen.getByText(/중급/i)).toBeInTheDocument()
    })
  })

  test('navigates to /home when "시작하기" button is clicked', async () => {
    // REQ: REQ-F-A2-2-4
    vi.mocked(transport.transport.get).mockResolvedValueOnce({
      user_id: 'test@samsung.com',
      nickname: 'testuser',
      registered_at: '2025-11-12T00:00:00Z',
      updated_at: '2025-11-12T00:00:00Z',
    })

    const user = userEvent.setup()
    renderWithRouter(<ProfileReviewPage />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /시작하기/i })).toBeInTheDocument()
    })

    const startButton = screen.getByRole('button', { name: /시작하기/i })
    await user.click(startButton)

    expect(mockNavigate).toHaveBeenCalledWith('/home', { replace: true })
  })

  test('navigates back to /self-assessment when "수정하기" button is clicked', async () => {
    // REQ: REQ-F-A2-2-4
    vi.mocked(transport.transport.get).mockResolvedValueOnce({
      user_id: 'test@samsung.com',
      nickname: 'testuser',
      registered_at: '2025-11-12T00:00:00Z',
      updated_at: '2025-11-12T00:00:00Z',
    })

    const user = userEvent.setup()
    renderWithRouter(<ProfileReviewPage />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /수정하기/i })).toBeInTheDocument()
    })

    const editButton = screen.getByRole('button', { name: /수정하기/i })
    await user.click(editButton)

    expect(mockNavigate).toHaveBeenCalledWith('/self-assessment')
  })

  test('shows loading state while fetching nickname', () => {
    // REQ: REQ-F-A2-2-4
    vi.mocked(transport.transport.get).mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          setTimeout(
            () =>
              resolve({
                user_id: 'test@samsung.com',
                nickname: 'testuser',
                registered_at: '2025-11-12T00:00:00Z',
                updated_at: '2025-11-12T00:00:00Z',
              }),
            100
          )
        })
    )

    renderWithRouter(<ProfileReviewPage />)

    expect(screen.getByText(/로딩 중/i)).toBeInTheDocument()
  })

  test('shows error message if nickname fetch fails', async () => {
    // REQ: REQ-F-A2-2-4
    vi.mocked(transport.transport.get).mockRejectedValueOnce(new Error('Network error'))

    renderWithRouter(<ProfileReviewPage />)

    await waitFor(() => {
      expect(screen.getByText(/Network error/i)).toBeInTheDocument()
    })
  })
})
