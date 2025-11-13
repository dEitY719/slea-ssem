// REQ: REQ-F-B4-1
import React, { useEffect, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { resultService, type GradeResult } from '../services'
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

// Helper: Convert English grade to Korean
const getGradeKorean = (grade: string): string => {
  const gradeMap: Record<string, string> = {
    Beginner: '시작자',
    Intermediate: '중급자',
    'Intermediate-Advanced': '중상급자',
    Advanced: '고급자',
    Elite: '엘리트',
  }
  return gradeMap[grade] || grade
}

// Helper: Get grade CSS class for color coding
const getGradeClass = (grade: string): string => {
  const classMap: Record<string, string> = {
    Beginner: 'grade-beginner',
    Intermediate: 'grade-intermediate',
    'Intermediate-Advanced': 'grade-intermediate-advanced',
    Advanced: 'grade-advanced',
    Elite: 'grade-elite',
  }
  return classMap[grade] || 'grade-default'
}

// Helper: Format decimal - remove trailing zero for integers
const formatDecimal = (value: number): string => {
  return Number(value.toFixed(1)).toString()
}

const TestResultsPage: React.FC = () => {
  const [resultData, setResultData] = useState<GradeResult | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as LocationState | null

  // Fetch results on mount
  useEffect(() => {
    const fetchResults = async () => {
      // Validate sessionId
      if (!state?.sessionId) {
        setError('세션 정보가 없습니다. 테스트를 다시 시작해주세요.')
        setIsLoading(false)
        return
      }

      setIsLoading(true)
      setError(null)

      try {
        const result = await resultService.getResults(state.sessionId)

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
  }, [state?.sessionId])

  // Retry handler
  const handleRetry = () => {
    setError(null)
    setIsLoading(true)
    // Re-trigger useEffect by forcing re-render
    setResultData(null)
    // Manually call fetch again
    if (state?.sessionId) {
      resultService
        .getResults(state.sessionId)
        .then(result => {
          setResultData(result)
          setIsLoading(false)
        })
        .catch(err => {
          setError(err instanceof Error ? err.message : '결과를 불러오는데 실패했습니다.')
          setIsLoading(false)
        })
    }
  }

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
            <button type="button" className="retry-button" onClick={handleRetry}>
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
        <div className={`grade-badge ${getGradeClass(resultData.grade)}`}>
          <div className="grade-icon">🏆</div>
          <div className="grade-info">
            <p className="grade-label">등급</p>
            <p className="grade-value">{getGradeKorean(resultData.grade)}</p>
            <p className="grade-english">{resultData.grade}</p>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="metrics-grid">
          {/* Score Card */}
          <div className="metric-card">
            <div className="metric-header">
              <span className="metric-icon">📊</span>
              <h2 className="metric-title">점수</h2>
            </div>
            <p className="metric-value">
              {formatDecimal(resultData.score)} <span className="metric-unit">/ 100</span>
            </p>
            <div className="progress-bar-container">
              <div
                className="progress-bar"
                role="progressbar"
                aria-valuenow={resultData.score}
                aria-valuemin={0}
                aria-valuemax={100}
                style={{ width: `${resultData.score}%` }}
              />
            </div>
          </div>

          {/* Rank Card */}
          <div className="metric-card">
            <div className="metric-header">
              <span className="metric-icon">📈</span>
              <h2 className="metric-title">순위</h2>
            </div>
            <p className="metric-value">
              {resultData.rank} <span className="metric-separator">/</span>{' '}
              {resultData.total_cohort_size}
            </p>
            <p className="metric-description">전체 응시자 중</p>
            {showConfidenceWarning && (
              <p className="confidence-warning">⚠️ 분포 신뢰도 낮음 (참고용)</p>
            )}
          </div>

          {/* Percentile Card */}
          <div className="metric-card">
            <div className="metric-header">
              <span className="metric-icon">🎯</span>
              <h2 className="metric-title">백분위</h2>
            </div>
            <p className="metric-value">{resultData.percentile_description}</p>
            <p className="metric-description">
              상위 {formatDecimal(100 - resultData.percentile)}% 내
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="action-buttons">
          <button
            type="button"
            className="primary-button"
            onClick={() => navigate('/home')}
          >
            홈화면으로 이동
          </button>
          <button
            type="button"
            className="secondary-button"
            onClick={() => navigate('/test', { state: { retake: true } })}
          >
            재응시하기
          </button>
        </div>
      </div>
    </main>
  )
}

export default TestResultsPage
