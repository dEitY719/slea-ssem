import { useEffect, useMemo } from 'react'
import { debugLog, debugWarn } from '../utils/logger'

const LATEST_SESSION_ID_KEY = 'latest_test_session_id'
const TEST_RESULTS_STATE_PREFIX = 'test_results_state_'

export type TestResultsLocationState = {
  sessionId: string
  surveyId?: string
  round?: number
  previousSessionId?: string
}

type PersistedStateResult = {
  persistedState: TestResultsLocationState | null
  round: number
  effectiveSessionId?: string
}

/**
 * Centralized hook for persisting and restoring TestResults location state.
 */
export const usePersistedTestResultsState = (
  state: TestResultsLocationState | null
): PersistedStateResult => {
  useEffect(() => {
    if (state?.sessionId) {
      sessionStorage.setItem(LATEST_SESSION_ID_KEY, state.sessionId)
      sessionStorage.setItem(`${TEST_RESULTS_STATE_PREFIX}${state.sessionId}`, JSON.stringify(state))
      debugLog('[TestResults] Saved state for session:', state.sessionId)
      debugLog('[TestResults] Full saved state:', state)
      debugLog('[TestResults] State has surveyId?', !!state.surveyId, 'Value:', state.surveyId)
    }
  }, [state])

  const { persistedState, latestSessionId } = useMemo(() => {
    if (state) {
      return { persistedState: state, latestSessionId: state.sessionId }
    }

    const sessionIdFromStorage = sessionStorage.getItem(LATEST_SESSION_ID_KEY) || undefined
    if (!sessionIdFromStorage) {
      debugWarn('[TestResults] No latest session ID found')
      return { persistedState: null, latestSessionId: undefined }
    }

    const stored = sessionStorage.getItem(`${TEST_RESULTS_STATE_PREFIX}${sessionIdFromStorage}`)
    if (stored) {
      try {
        const restoredState = JSON.parse(stored) as TestResultsLocationState
        debugLog('[TestResults] Restored state from sessionStorage:', restoredState)
        return { persistedState: restoredState, latestSessionId: sessionIdFromStorage }
      } catch {
        console.error('[TestResults] Failed to parse stored state')
        return { persistedState: null, latestSessionId: sessionIdFromStorage }
      }
    }

    return { persistedState: null, latestSessionId: sessionIdFromStorage }
  }, [state])

  const round = persistedState?.round || 1
  const effectiveSessionId = persistedState?.sessionId || latestSessionId

  return { persistedState, round, effectiveSessionId }
}
