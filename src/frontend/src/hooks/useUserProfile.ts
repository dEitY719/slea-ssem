// REQ: REQ-F-A2-1
import { useState, useCallback } from 'react'
import { getToken } from '../utils/auth'

/**
 * User profile response from GET /api/profile/nickname
 */
interface UserProfileResponse {
  user_id: string
  nickname: string | null
  registered_at: string | null
  updated_at: string | null
}

/**
 * Hook for fetching and managing user profile information
 *
 * REQ: REQ-F-A2-1 - Check if user has set nickname
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
      const token = getToken()
      if (!token) {
        throw new Error('No authentication token found')
      }

      const response = await fetch('/api/profile/nickname', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to fetch user profile')
      }

      const data: UserProfileResponse = await response.json()
      setNickname(data.nickname)
      setLoading(false)
      return data.nickname  // ✅ Return the value directly
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
