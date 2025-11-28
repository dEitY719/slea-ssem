// REQ: REQ-F-B5-1
import React from 'react'
import { 
  ChartBarIcon, 
  SparklesIcon, 
  ArrowUpIcon, 
  ArrowDownIcon, 
  ArrowRightIcon 
} from '@heroicons/react/24/outline'
import { Grade, PreviousResult } from '../../services/resultService'
import './ComparisonSection.css'

interface ComparisonSectionProps {
  currentGrade: Grade
  currentScore: number
  previousResult: PreviousResult | null
}

/**
 * Comparison Section Component
 * Displays comparison between previous and current test results
 *
 * REQ: REQ-F-B5-1 - 이전 응시 정보 비교 섹션
 */
export const ComparisonSection: React.FC<ComparisonSectionProps> = ({
  currentGrade,
  currentScore,
  previousResult,
}) => {
  // First attempt - no previous result
  if (!previousResult) {
    return (
      <div className="comparison-section">
        <h2 className="comparison-title">
          <ChartBarIcon className="section-icon" />
          성적 비교
        </h2>
        <div className="first-attempt">
          <p className="first-attempt-message">
            <SparklesIcon className="message-icon" />
            첫 응시입니다
          </p>
          <div className="current-only">
            <div className="metric">
              <span className="metric-label">현재 등급:</span>
              <span className="metric-value">{currentGrade}</span>
            </div>
            <div className="metric">
              <span className="metric-label">현재 점수:</span>
              <span className="metric-value">{currentScore}점</span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Calculate changes
  const gradeChanged = previousResult.grade !== currentGrade
  const scoreDiff = currentScore - previousResult.score
  const scoreChanged = scoreDiff !== 0

  // Determine trend (improvement, decline, no change)
  const gradeOrder: Record<Grade, number> = {
    Beginner: 1,
    Intermediate: 2,
    'Inter-Advanced': 3,
    Advanced: 4,
    Elite: 5,
  }
  const gradeImproved = gradeOrder[currentGrade] > gradeOrder[previousResult.grade]
  const gradeDeclined = gradeOrder[currentGrade] < gradeOrder[previousResult.grade]

  // Overall trend (score is primary indicator)
  const improved = scoreDiff > 0
  const declined = scoreDiff < 0

  // Format test date
  const testDate = new Date(previousResult.test_date)
  const formattedDate = testDate.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })

  return (
    <div className="comparison-section">
      <h2 className="comparison-title">
        <ChartBarIcon className="section-icon" />
        성적 비교
      </h2>
      <p className="previous-test-date">이전 테스트: {formattedDate}</p>

      <div className="comparison-content">
        {/* Grade Comparison */}
        <div className={`comparison-item ${gradeChanged ? (gradeImproved ? 'improved' : gradeDeclined ? 'declined' : 'unchanged') : 'unchanged'}`}>
          <span className="comparison-label">등급</span>
          {gradeChanged ? (
            <div className="comparison-change">
              <span className="old-value">{previousResult.grade}</span>
              {gradeImproved ? (
                <ArrowUpIcon className="arrow arrow-up" />
              ) : gradeDeclined ? (
                <ArrowDownIcon className="arrow arrow-down" />
              ) : (
                <ArrowRightIcon className="arrow arrow-right" />
              )}
              <span className="new-value">{currentGrade}</span>
            </div>
          ) : (
            <div className="comparison-unchanged">
              <span className="value">{currentGrade}</span>
              <ArrowRightIcon className="arrow arrow-right" />
              <span className="status">(변동 없음)</span>
            </div>
          )}
        </div>

        {/* Score Comparison */}
        <div className={`comparison-item ${scoreChanged ? (improved ? 'improved' : 'declined') : 'unchanged'}`}>
          <span className="comparison-label">점수</span>
          {scoreChanged ? (
            <div className="comparison-change">
              <span className="old-value">{previousResult.score}점</span>
              {improved ? (
                <ArrowUpIcon className="arrow arrow-up" />
              ) : (
                <ArrowDownIcon className="arrow arrow-down" />
              )}
              <span className="new-value">{currentScore}점</span>
              <span className={`diff ${improved ? 'positive' : 'negative'}`}>
                ({scoreDiff > 0 ? '+' : ''}{scoreDiff}점)
              </span>
            </div>
          ) : (
            <div className="comparison-unchanged">
              <span className="value">{currentScore}점</span>
              <ArrowRightIcon className="arrow arrow-right" />
              <span className="status">(변동 없음)</span>
            </div>
          )}
        </div>
      </div>

      {/* Summary message */}
      {improved && (
        <div className="summary-message improved">
          <SparklesIcon className="summary-icon" />
          이전보다 {Math.abs(scoreDiff)}점 향상되었습니다!
        </div>
      )}
      {declined && (
        <div className="summary-message declined">
          이전보다 {Math.abs(scoreDiff)}점 낮아졌습니다. 다시 도전해보세요!
        </div>
      )}
      {!scoreChanged && !gradeChanged && (
        <div className="summary-message unchanged">
          이전과 동일한 성적입니다.
        </div>
      )}
    </div>
  )
}
