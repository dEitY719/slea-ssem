import React from 'react'
import type { Grade } from '../../services/resultService'
import { getGradeKorean } from '../../utils/gradeHelpers'

interface GradeBarProps {
  grade: Grade
  count: number
  percentage: number
  barHeightPercentage: number
  isUserGrade: boolean
}

export const GradeBar: React.FC<GradeBarProps> = ({
  grade,
  count,
  percentage,
  barHeightPercentage,
  isUserGrade,
}) => {
  const gradeKorean = getGradeKorean(grade)
  const barStyle = {
    '--bar-height': `${barHeightPercentage}%`,
  } as React.CSSProperties

  return (
    <div
      className={`distribution-bar ${isUserGrade ? 'user-current-grade' : ''}`}
      style={barStyle}
    >
      <div className="bar-label">
        <span className="bar-grade-name">{gradeKorean}</span>
        {isUserGrade && (
          <span className="bar-user-indicator" aria-label="Your current position">
            📍 현재 위치
          </span>
        )}
      </div>

      <div className="bar-container">
        <div
          className="bar-fill"
          aria-label={`${gradeKorean}: ${count} people, ${percentage}%`}
        >
          <div className="bar-value">
            <span className="bar-count">{count}</span>
            <span className="bar-percentage">({percentage}%)</span>
          </div>
        </div>
      </div>

      <div className="bar-grade-english">{grade}</div>
    </div>
  )
}
