// REQ: REQ-F-B4-1, REQ-F-B4-3, REQ-F-B4-4, REQ-F-B5-1, REQ-F-B5-Retake-1
import React, { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { ArrowPathIcon, HomeIcon } from '@heroicons/react/24/outline'
import { PageLayout } from '../components'
import { useTestResults } from '../hooks/useTestResults'
import { GradeBadge, MetricCard, ActionButtons, GradeDistributionChart, ComparisonSection } from '../components/TestResults'
import { resultService, type PreviousResult } from '../services/resultService'
import './TestResultsPage.css'

/**
 * Test Results Page Component
 *
 * REQ: REQ-F-B4-1 - 최종 등급(1~5), 점수, 상대 순위, 백분위를 시각적으로 표시
 *
 * Features:
 * - Display final grade with color-coded badge
 * - Display score with progress bar
 * - Display relative rank (e.g., "3 / 506")
 * - Display percentile (e.g., "상위 28%")
 * - All metrics displayed simultaneously and visually
 *
 * Route: /test-results
 */

type LocationState = {
  sessionId: string
  surveyId?: string
  round?: number  // REQ-F-B5-Retake-4: Track round for Round 2 flow
  previousSessionId?: string  // REQ-F-B5-Retake-4: For Round 2 results
}

const TestResultsPage: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as LocationState | null

  // REQ-F-B5-Retake-4: Persist state to sessionStorage to prevent loss on navigation
  // Save state to sessionStorage when available
  React.useEffect(() => {
    if (state?.sessionId) {
      // Save latest sessionId for key lookup
      sessionStorage.setItem('latest_test_session_id', state.sessionId)
      // Save full state with sessionId-based key
      sessionStorage.setItem(`test_results_state_${state.sessionId}`, JSON.stringify(state))
      console.log('[TestResults] Saved state for session:', state.sessionId)
    }
  }, [state])

  // Get state from location.state or sessionStorage
  const getPersistedState = (): LocationState | null => {
    if (state) return state

    // Get latest sessionId to construct correct key
    const latestSessionId = sessionStorage.getItem('latest_test_session_id')
    if (!latestSessionId) {
      console.warn('[TestResults] No latest session ID found')
      return null
    }

    const stored = sessionStorage.getItem(`test_results_state_${latestSessionId}`)
    if (stored) {
      try {
        const restoredState = JSON.parse(stored) as LocationState
        console.log('[TestResults] Restored state from sessionStorage:', restoredState)
        return restoredState
      } catch {
        console.error('[TestResults] Failed to parse stored state')
        return null
      }
    }
    return null
  }

  // Get round from persisted state
  const getRound = (): number => {
    const persistedState = getPersistedState()
    return persistedState?.round || 1
  }

  // Custom hook for data fetching with retry logic
  const { resultData, isLoading, error, retry } = useTestResults(state?.sessionId)

  // REQ-F-B5-1: Fetch previous result for comparison
  const [previousResult, setPreviousResult] = useState<PreviousResult | null>(null)
  const [isPreviousLoading, setIsPreviousLoading] = useState(true)

  useEffect(() => {
    const fetchPreviousResult = async () => {
      setIsPreviousLoading(true)
      try {
        const result = await resultService.getPreviousResult()
        setPreviousResult(result)
      } catch (err) {
        // Silently fail - comparison section will handle null
        setPreviousResult(null)
      } finally {
        setIsPreviousLoading(false)
      }
    }

    fetchPreviousResult()
  }, [])

  // Loading state
  if (isLoading) {
    return (
      <PageLayout mainClassName="results-page" containerClassName="results-container">
        <p className="loading-text">결과를 불러오는 중입니다...</p>
      </PageLayout>
    )
  }

  // Error state
  if (error) {
    return (
      <PageLayout mainClassName="results-page" containerClassName="results-container">
        <div className="error-container">
          <p className="error-message">{error}</p>
          <button type="button" className="retry-button" onClick={retry}>
            <ArrowPathIcon className="button-icon" />
            다시 시도
          </button>
          <button
            type="button"
            className="back-button"
            onClick={() => navigate('/home')}
          >
            <HomeIcon className="button-icon" />
            홈화면으로 돌아가기
          </button>
        </div>
      </PageLayout>
    )
  }

  // No data state (shouldn't happen if loading/error handled correctly)
  if (!resultData) {
    return (
      <PageLayout mainClassName="results-page" containerClassName="results-container">
        <p className="error-message">결과 데이터가 없습니다.</p>
      </PageLayout>
    )
  }

  // Show confidence warning for small cohort
  const showConfidenceWarning = resultData.total_cohort_size < 100

  return (
    <PageLayout mainClassName="results-page" containerClassName="results-container">
      <h1 className="results-title">테스트 결과</h1>

      {/* Grade Badge (Large, Prominent) */}
      <GradeBadge grade={resultData.grade} />

      {/* Metrics Grid */}
      <div className="metrics-grid">
        <MetricCard type="score" title="점수" score={resultData.score} />

        <MetricCard
          type="rank"
          title="순위"
          rank={resultData.rank}
          totalCohortSize={resultData.total_cohort_size}
          showConfidenceWarning={showConfidenceWarning}
        />

        <MetricCard
          type="percentile"
          title="백분위"
          percentileDescription={resultData.percentile_description}
          percentile={resultData.percentile}
        />
      </div>

      {/* Grade Distribution Chart - REQ: REQ-F-B4-3, REQ-F-B4-4 */}
      {resultData.grade_distribution && (
        <GradeDistributionChart
          distribution={resultData.grade_distribution}
          userGrade={resultData.grade}
          rank={resultData.rank}
          totalCohortSize={resultData.total_cohort_size}
          percentileDescription={resultData.percentile_description}
          showConfidenceWarning={showConfidenceWarning}
        />
      )}

      {/* Comparison Section - REQ: REQ-F-B5-1 */}
      {!isPreviousLoading && (
        <ComparisonSection
          currentGrade={resultData.grade}
          currentScore={resultData.score}
          previousResult={previousResult}
        />
      )}

      {/* Action Buttons */}
      <ActionButtons
        round={getRound()}
        onGoHome={() => navigate('/home')}
        onRetake={async () => {
          // REQ-F-B5-Retake-4: Round 1 완료 시 Round 2 adaptive 시작
          const persistedState = getPersistedState()
          const currentRound = getRound()

          if (currentRound === 1) {
            // Round 1 → Round 2 adaptive
            if (!persistedState?.surveyId || !persistedState?.sessionId) {
              console.error('[Retake] Missing surveyId or sessionId')
              navigate('/home')
              return
            }

            console.log('[Retake] Round 1 completed, starting Round 2')
            navigate('/test', {
              state: {
                surveyId: persistedState.surveyId,
                round: 2,
                previousSessionId: persistedState.sessionId,  // Pass Round 1 session_id for adaptive
              },
            })
          } else {
            // Round 2 완료 후 재응시는 없음 (버튼도 숨겨져 있어야 함)
            // 혹시 호출되면 fallback으로 home으로 이동
            console.warn('[Retake] Unexpected retake after Round 2, round:', currentRound)
            navigate('/home')
          }
        }}
        onViewExplanations={() => {
          // REQ: REQ-F-B4-7 - Navigate to explanation page
          const persistedState = getPersistedState()
          if (persistedState?.sessionId) {
            navigate(`/test-explanations/${persistedState.sessionId}`)
          }
        }}
      />
    </PageLayout>
  )
}

export default TestResultsPage
