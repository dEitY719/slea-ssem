// REQ: REQ-F-A2-2
import { useState, useCallback } from 'react'
import { profileService } from '../services'

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
 * REQ: REQ-F-A2-3 - 닉네임 유효성 검사 (백엔드에서 처리)
 *
 * Validation:
 * - Frontend: Basic empty check only
 * - Backend: All validation (length, characters, profanity filter)
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

    // Basic empty check only
    if (!nickname || nickname.trim().length === 0) {
      setCheckStatus('error')
      setErrorMessage('닉네임을 입력해주세요.')
      return
    }

    // All validation (length, characters, profanity) is handled by backend
    // Call API to check availability
    setCheckStatus('checking')

    try {
      const response = await profileService.checkNickname(nickname)

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
