// REQ: REQ-F-B4-1, REQ-F-B4-3, REQ-F-B4-4, REQ-F-B5-1, REQ-F-B5-Retake-1
import React, { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { ArrowPathIcon, HomeIcon } from '@heroicons/react/24/outline'
import { PageLayout } from '../components'
import { useTestResults } from '../hooks/useTestResults'
import { GradeBadge, MetricCard, ActionButtons, GradeDistributionChart, ComparisonSection } from '../components/TestResults'
import { resultService, type PreviousResult } from '../services/resultService'
import { profileService } from '../services/profileService'
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
}

const TestResultsPage: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as LocationState | null

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
        onGoHome={() => navigate('/home')}
        onRetake={async () => {
          // REQ-F-B5-Retake-1: Load profile history and navigate to career info with pre-filled data
          try {
            // Call GET /profile/history to load previous assessment data
            const profileHistory = await profileService.getProfileHistory()

            console.log('[Retake] Loaded profile history:', profileHistory)

            // Navigate to CareerInfoPage with pre-filled data
            navigate('/career-info', {
              state: {
                retakeMode: true,
                profileData: {
                  surveyId: profileHistory.survey.survey_id,
                  level: profileHistory.survey.level,
                  career: profileHistory.survey.career,
                  jobRole: profileHistory.survey.job_role,
                  duty: profileHistory.survey.duty,
                  interests: profileHistory.survey.interests,
                },
              },
            })
          } catch (err) {
            console.error('[Retake] Failed to load profile history:', err)
            // Fallback: navigate to career-info without pre-filled data
            navigate('/career-info', {
              state: {
                retakeMode: true,
              },
            })
          }
        }}
        onViewExplanations={() => {
          // REQ: REQ-F-B4-7 - Navigate to explanation page
          if (state?.sessionId) {
            navigate(`/test-explanations/${state.sessionId}`)
          }
        }}
      />
    </PageLayout>
  )
}

export default TestResultsPage
