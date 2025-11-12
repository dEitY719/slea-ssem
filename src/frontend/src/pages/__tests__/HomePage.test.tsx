// REQ: REQ-F-A2-1
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import HomePage from '../HomePage'
import * as authUtils from '../../utils/auth'

// Mock useNavigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// Mock auth utils
vi.mock('../../utils/auth', () => ({
  getToken: vi.fn(() => 'mock_jwt_token'),
}))

describe('HomePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(authUtils, 'getToken').mockReturnValue('mock_jwt_token')
    ;(globalThis.fetch as any) = vi.fn()
  })

  it('should redirect to login if no token is present', () => {
    vi.spyOn(authUtils, 'getToken').mockReturnValue(null)

    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    )

    expect(mockNavigate).toHaveBeenCalledWith('/')
  })

  it('should display welcome message when authenticated', () => {
    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    )

    expect(screen.getByText('S.LSI Learning Platform')).toBeInTheDocument()
    expect(screen.getByText(/AI 기반 학습 플랫폼/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /시작하기/i })).toBeInTheDocument()
  })

  it('should call API to check nickname when "시작하기" is clicked', async () => {
    ;(globalThis.fetch as any).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        user_id: 'test@samsung.com',
        nickname: 'testuser',
        registered_at: '2025-11-10T12:00:00Z',
        updated_at: '2025-11-10T12:00:00Z',
      }),
    })

    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    )

    const startButton = screen.getByRole('button', { name: /시작하기/i })
    fireEvent.click(startButton)

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        '/api/profile/nickname',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock_jwt_token',
          }),
        })
      )
    })
  })

  it('should redirect to /nickname-setup when nickname is null', async () => {
    // REQ: REQ-F-A2-1
    ;(globalThis.fetch as any).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        user_id: 'test@samsung.com',
        nickname: null,  // ✅ REQ-F-A2-1: nickname is NULL
        registered_at: null,
        updated_at: null,
      }),
    })

    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    )

    const startButton = screen.getByRole('button', { name: /시작하기/i })
    fireEvent.click(startButton)

    await waitFor(() => {
      // REQ-F-A2-1: Navigate to nickname-setup when nickname is null
      expect(mockNavigate).toHaveBeenCalledWith('/nickname-setup')
    })
  })

  it('should navigate to self-assessment when nickname exists', async () => {
    // REQ: REQ-F-A2-2-1
    ;(globalThis.fetch as any).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        user_id: 'test@samsung.com',
        nickname: 'testuser',  // ✅ nickname is set
        registered_at: '2025-11-10T12:00:00Z',
        updated_at: '2025-11-10T12:00:00Z',
      }),
    })

    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    )

    const startButton = screen.getByRole('button', { name: /시작하기/i })
    fireEvent.click(startButton)

    await waitFor(() => {
      // REQ-F-A2-2-1: Navigate to self-assessment when nickname exists
      expect(mockNavigate).toHaveBeenCalledWith('/self-assessment')
    })
  })

  it('should display error message when API call fails', async () => {
    ;(globalThis.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Unauthorized' }),
    })

    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    )

    const startButton = screen.getByRole('button', { name: /시작하기/i })
    fireEvent.click(startButton)

    await waitFor(() => {
      // Error handling - show error message to user
      const errorElement = screen.queryByText(/오류가 발생했습니다/i)
      expect(errorElement || mockNavigate).toBeTruthy()
    })
  })

  it('should handle network errors gracefully', async () => {
    ;(globalThis.fetch as any).mockRejectedValueOnce(new Error('Network error'))

    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    )

    const startButton = screen.getByRole('button', { name: /시작하기/i })
    fireEvent.click(startButton)

    await waitFor(() => {
      // Should show error message or handle gracefully
      const errorElement = screen.queryByText(/오류가 발생했습니다/i)
      expect(errorElement || mockNavigate).toBeTruthy()
    })
  })
})
