// REQ: REQ-F-B4-1
import { useState, useEffect } from 'react'
import { resultService, type GradeResult } from '../services'

interface UseTestResultsReturn {
  resultData: GradeResult | null
  isLoading: boolean
  error: string | null
  retry: () => void
}

/**
 * Custom hook for fetching test results with retry logic
 *
 * @param sessionId - Test session ID from location state
 * @returns Test result data, loading state, error state, and retry function
 */
export const useTestResults = (sessionId: string | undefined): UseTestResultsReturn => {
  const [resultData, setResultData] = useState<GradeResult | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [retryTrigger, setRetryTrigger] = useState(0)

  useEffect(() => {
    const fetchResults = async () => {
      // Validate sessionId
      if (!sessionId) {
        setError('세션 정보가 없습니다. 테스트를 다시 시작해주세요.')
        setIsLoading(false)
        return
      }

      setIsLoading(true)
      setError(null)

      try {
        const result = await resultService.getResults(sessionId)

        // Validate required fields
        if (
          !result.grade ||
          result.score === undefined ||
          result.rank === undefined ||
          result.percentile === undefined
        ) {
          throw new Error('결과 데이터가 올바르지 않습니다.')
        }

        setResultData(result)
        setIsLoading(false)
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message.includes('Not Found')
              ? '결과를 찾을 수 없습니다. 테스트를 완료했는지 확인해주세요.'
              : `결과를 불러오는데 실패했습니다: ${err.message}`
            : '결과를 불러오는데 실패했습니다.'
        setError(message)
        setIsLoading(false)
      }
    }

    fetchResults()
  }, [sessionId, retryTrigger])

  const retry = () => {
    setResultData(null)
    setError(null)
    setRetryTrigger(prev => prev + 1)
  }

  return { resultData, isLoading, error, retry }
}
