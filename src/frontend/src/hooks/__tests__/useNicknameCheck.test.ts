// REQ: REQ-F-A2-2
import { renderHook, act, waitFor } from '@testing-library/react'
import { describe, test, expect, vi, beforeEach } from 'vitest'
import { useNicknameCheck } from '../useNicknameCheck'
import * as transport from '../../lib/transport'

// Mock transport
vi.mock('../../lib/transport', () => ({
  transport: {
    post: vi.fn(),
  },
}))

describe('useNicknameCheck', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  test('initial state is correct', () => {
    // REQ: REQ-F-A2-2
    const { result } = renderHook(() => useNicknameCheck())

    expect(result.current.nickname).toBe('')
    expect(result.current.checkStatus).toBe('idle')
    expect(result.current.errorMessage).toBeNull()
    expect(result.current.suggestions).toEqual([])
  })

  test('setNickname updates nickname value', () => {
    // REQ: REQ-F-A2-2
    const { result } = renderHook(() => useNicknameCheck())

    act(() => {
      result.current.setNickname('john_doe')
    })

    expect(result.current.nickname).toBe('john_doe')
  })

  test('checkNickname validates length (too short)', async () => {
    // REQ: REQ-F-A2-2 (validation)
    const { result } = renderHook(() => useNicknameCheck())

    act(() => {
      result.current.setNickname('ab')
    })

    await act(async () => {
      await result.current.checkNickname()
    })

    expect(result.current.checkStatus).toBe('error')
    expect(result.current.errorMessage).toContain('3자 이상')
  })

  test('checkNickname validates invalid characters', async () => {
    // REQ: REQ-F-A2-2 (validation)
    const { result } = renderHook(() => useNicknameCheck())

    act(() => {
      result.current.setNickname('john@doe')
    })

    await act(async () => {
      await result.current.checkNickname()
    })

    expect(result.current.checkStatus).toBe('error')
    expect(result.current.errorMessage).toContain('영문자, 숫자, 언더스코어')
  })

  test('checkNickname calls API and updates status to available', async () => {
    // REQ: REQ-F-A2-2
    const mockResponse = { available: true, suggestions: [] }
    vi.mocked(transport.transport.post).mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useNicknameCheck())

    act(() => {
      result.current.setNickname('john_doe')
    })

    await act(async () => {
      await result.current.checkNickname()
    })

    expect(transport.transport.post).toHaveBeenCalledWith('/profile/nickname/check', {
      nickname: 'john_doe',
    })
    expect(result.current.checkStatus).toBe('available')
    expect(result.current.errorMessage).toBeNull()
  })

  test('checkNickname updates status to taken when nickname exists', async () => {
    // REQ: REQ-F-A2-2
    const mockResponse = {
      available: false,
      suggestions: ['john_doe1', 'john_doe2', 'john_doe3'],
    }
    vi.mocked(transport.transport.post).mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useNicknameCheck())

    act(() => {
      result.current.setNickname('existing_user')
    })

    await act(async () => {
      await result.current.checkNickname()
    })

    expect(result.current.checkStatus).toBe('taken')
    expect(result.current.suggestions).toEqual(['john_doe1', 'john_doe2', 'john_doe3'])
  })

  test('check result displays within 1 second', async () => {
    // REQ: REQ-F-A2-2 (수용 기준: 1초 내 응답)
    const mockResponse = { available: true, suggestions: [] }
    vi.mocked(transport.transport.post).mockResolvedValue(mockResponse)

    const { result } = renderHook(() => useNicknameCheck())

    act(() => {
      result.current.setNickname('john_doe')
    })

    const startTime = Date.now()

    await act(async () => {
      await result.current.checkNickname()
    })

    const endTime = Date.now()
    const elapsed = endTime - startTime

    expect(elapsed).toBeLessThan(1000) // 1초 이내
    expect(result.current.checkStatus).toBe('available')
  })

  test('checkNickname handles API errors gracefully', async () => {
    // REQ: REQ-F-A2-2
    vi.mocked(transport.transport.post).mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => useNicknameCheck())

    act(() => {
      result.current.setNickname('john_doe')
    })

    await act(async () => {
      await result.current.checkNickname()
    })

    expect(result.current.checkStatus).toBe('error')
    expect(result.current.errorMessage).toBeTruthy()
  })
})
