// REQ: REQ-F-A2-2
import { useState, useCallback } from 'react'
import { transport } from '../lib/transport'

/**
 * Nickname check response from POST /profile/nickname/check
 */
interface NicknameCheckResponse {
  available: boolean
  suggestions: string[]
}

/**
 * Check status type
 */
type CheckStatus = 'idle' | 'checking' | 'available' | 'taken' | 'error'

/**
 * Hook result interface
 */
export interface UseNicknameCheckResult {
  nickname: string
  setNickname: (value: string) => void
  checkStatus: CheckStatus
  errorMessage: string | null
  suggestions: string[]
  checkNickname: () => Promise<void>
  setManualError: (message: string) => void
}

/**
 * Hook for checking nickname availability
 *
 * REQ: REQ-F-A2-2 - 닉네임 입력 필드와 "중복 확인" 버튼 제공
 *
 * Validation rules:
 * - Length: 3-30 characters
 * - Characters: Letters (a-z, A-Z), numbers (0-9), underscore (_)
 *
 * Usage:
 * ```tsx
 * const { nickname, setNickname, checkStatus, checkNickname } = useNicknameCheck()
 *
 * <input value={nickname} onChange={(e) => setNickname(e.target.value)} />
 * <button onClick={checkNickname}>중복 확인</button>
 * ```
 */
export function useNicknameCheck(): UseNicknameCheckResult {
  const [nickname, setNicknameState] = useState('')
  const [checkStatus, setCheckStatus] = useState<CheckStatus>('idle')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [suggestions, setSuggestions] = useState<string[]>([])

  const setNickname = useCallback(
    (value: string) => {
      setNicknameState(value)
      setCheckStatus('idle')
      setErrorMessage(null)
      setSuggestions([])
    },
    [setNicknameState, setCheckStatus, setErrorMessage, setSuggestions]
  )

  const setManualError = useCallback((message: string) => {
    setCheckStatus('error')
    setErrorMessage(message)
    setSuggestions([])
  }, [])

  const checkNickname = useCallback(async (): Promise<void> => {
    // Reset state
    setErrorMessage(null)
    setSuggestions([])

    // Validate length (3-30 characters)
    if (nickname.length < 3) {
      setCheckStatus('error')
      setErrorMessage('닉네임은 3자 이상이어야 합니다.')
      return
    }

    if (nickname.length > 30) {
      setCheckStatus('error')
      setErrorMessage('닉네임은 30자 이하여야 합니다.')
      return
    }

    // Validate characters (letters, numbers, underscore only)
    const validPattern = /^[a-zA-Z0-9_]+$/
    if (!validPattern.test(nickname)) {
      setCheckStatus('error')
      setErrorMessage('닉네임은 영문자, 숫자, 언더스코어만 사용 가능합니다.')
      return
    }

    // Call API to check availability
    setCheckStatus('checking')

    try {
      const response = await transport.post<NicknameCheckResponse>(
        '/profile/nickname/check',
        { nickname }
      )

      if (response.available) {
        setCheckStatus('available')
      } else {
        setCheckStatus('taken')
        setSuggestions(response.suggestions)
      }
    } catch (err) {
      setCheckStatus('error')
      const errorMsg = err instanceof Error ? err.message : '닉네임 확인에 실패했습니다.'
      setErrorMessage(errorMsg)
    }
  }, [nickname])

  return {
    nickname,
    setNickname,
    checkStatus,
    errorMessage,
    suggestions,
    checkNickname,
    setManualError,
  }
}
