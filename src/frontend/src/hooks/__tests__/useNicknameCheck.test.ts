// REQ: REQ-F-A2-2
import { renderHook, act } from '@testing-library/react'
import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest'
import { useNicknameCheck } from '../useNicknameCheck'
import { mockConfig } from '../../lib/transport'

describe('useNicknameCheck', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.setItem('slea_ssem_api_mock', 'true')
    mockConfig.delay = 0
    mockConfig.simulateError = false
  })

  afterEach(() => {
    localStorage.removeItem('slea_ssem_api_mock')
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

  test('checkNickname marks nickname as available when not taken', async () => {
    // REQ: REQ-F-A2-2
    const { result } = renderHook(() => useNicknameCheck())

    act(() => {
      result.current.setNickname('new_user')
    })

    await act(async () => {
      await result.current.checkNickname()
    })

    expect(result.current.checkStatus).toBe('available')
    expect(result.current.errorMessage).toBeNull()
  })

    test('checkNickname updates status to taken when nickname exists', async () => {
    // REQ: REQ-F-A2-2
    const { result } = renderHook(() => useNicknameCheck())

    act(() => {
        result.current.setNickname('existing_user')
    })

    await act(async () => {
      await result.current.checkNickname()
    })

    expect(result.current.checkStatus).toBe('taken')
      expect(result.current.suggestions).toEqual([
        'existing_user_1',
        'existing_user_2',
        'existing_user_3',
      ])
  })

  test('check result displays within 1 second', async () => {
    // REQ: REQ-F-A2-2 (수용 기준: 1초 내 응답)
    const { result } = renderHook(() => useNicknameCheck())

    act(() => {
      result.current.setNickname('speed_test')
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
    mockConfig.simulateError = true

    const { result } = renderHook(() => useNicknameCheck())

    act(() => {
      result.current.setNickname('john_doe')
    })

    await act(async () => {
      await result.current.checkNickname()
    })

    expect(result.current.checkStatus).toBe('error')
    expect(result.current.errorMessage).toContain('Mock Transport')
    mockConfig.simulateError = false
  })
})
