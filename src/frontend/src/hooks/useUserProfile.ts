// REQ: REQ-F-A2-1
import { useState, useCallback } from 'react'
import { profileService, type UserProfileResponse } from '../services'

/**
 * Hook for fetching and managing user profile information
 *
 * REQ: REQ-F-A2-1 - Check if user has set nickname
 *
 * Uses Transport pattern for API calls:
 * - Real backend in production
 * - Mock data in development (when VITE_MOCK_API=true or ?api_mock=true)
 *
 * Usage:
 * ```tsx
 * const { nickname, loading, error, checkNickname } = useUserProfile()
 *
 * await checkNickname()
 * if (nickname === null) {
 *   // User hasn't set nickname yet
 *   navigate('/signup')
 * } else {
 *   // User has nickname, proceed
 * }
 * ```
 */
export function useUserProfile() {
  const [nickname, setNickname] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const checkNickname = useCallback(async (): Promise<string | null> => {
    setLoading(true)
    setError(null)

    try {
      // Use service layer for API calls
      const data = await profileService.getNickname()

      setNickname(data.nickname)
      setLoading(false)
      return data.nickname
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred'
      setError(errorMessage)
      setLoading(false)
      throw err
    }
  }, [])

  return {
    nickname,
    loading,
    error,
    checkNickname,
  }
}
