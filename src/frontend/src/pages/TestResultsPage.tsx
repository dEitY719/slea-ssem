// REQ: REQ-F-B4-1, REQ-F-B4-3
import React from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useTestResults } from '../hooks/useTestResults'
import { GradeBadge, MetricCard, ActionButtons, GradeDistributionChart } from '../components/TestResults'
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
}

const TestResultsPage: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as LocationState | null

  // Custom hook for data fetching with retry logic
  const { resultData, isLoading, error, retry } = useTestResults(state?.sessionId)

  // Loading state
  if (isLoading) {
    return (
      <main className="results-page">
        <div className="results-container">
          <p className="loading-text">결과를 불러오는 중입니다...</p>
        </div>
      </main>
    )
  }

  // Error state
  if (error) {
    return (
      <main className="results-page">
        <div className="results-container">
          <div className="error-container">
            <p className="error-message">{error}</p>
            <button type="button" className="retry-button" onClick={retry}>
              다시 시도
            </button>
            <button
              type="button"
              className="back-button"
              onClick={() => navigate('/home')}
            >
              홈화면으로 돌아가기
            </button>
          </div>
        </div>
      </main>
    )
  }

  // No data state (shouldn't happen if loading/error handled correctly)
  if (!resultData) {
    return (
      <main className="results-page">
        <div className="results-container">
          <p className="error-message">결과 데이터가 없습니다.</p>
        </div>
      </main>
    )
  }

  // Show confidence warning for small cohort
  const showConfidenceWarning =
    resultData.total_cohort_size < 100 || resultData.percentile_confidence === 'medium'

  return (
    <main className="results-page">
      <div className="results-container">
        <h1 className="results-title">테스트 결과</h1>

        {/* Grade Badge (Large, Prominent) */}
        <GradeBadge grade={resultData.grade} />

        {/* Metrics Grid */}
        <div className="metrics-grid">
          <MetricCard type="score" icon="📊" title="점수" score={resultData.score} />

          <MetricCard
            type="rank"
            icon="📈"
            title="순위"
            rank={resultData.rank}
            totalCohortSize={resultData.total_cohort_size}
            showConfidenceWarning={showConfidenceWarning}
          />

          <MetricCard
            type="percentile"
            icon="🎯"
            title="백분위"
            percentileDescription={resultData.percentile_description}
            percentile={resultData.percentile}
          />
        </div>

        {/* Grade Distribution Chart - REQ: REQ-F-B4-3 */}
        <GradeDistributionChart
          distribution={resultData.grade_distribution}
          userGrade={resultData.grade}
          rank={resultData.rank}
          totalCohortSize={resultData.total_cohort_size}
          percentileDescription={resultData.percentile_description}
        />

        {/* Action Buttons */}
        <ActionButtons
          onGoHome={() => navigate('/home')}
          onRetake={() => navigate('/test', { state: { retake: true } })}
        />
      </div>
    </main>
  )
}

export default TestResultsPage
