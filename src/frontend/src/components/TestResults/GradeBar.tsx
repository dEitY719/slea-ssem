import React from 'react'
import { MapPinIcon } from '@heroicons/react/24/solid'
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
  const safeCount = Number.isFinite(count) && count >= 0 ? count : 0
  const safePercentage = Number.isFinite(percentage) && percentage >= 0 ? percentage : 0
  const normalizedHeight = Number.isFinite(barHeightPercentage)
    ? Math.min(Math.max(barHeightPercentage, 0), 100)
    : 0

  const barStyle = {
    '--bar-height': `${normalizedHeight}%`,
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
            <MapPinIcon className="pin-icon" />
            현재 위치
          </span>
        )}
      </div>

      <div className="bar-container">
        <div
          className="bar-fill"
          aria-label={`${gradeKorean}: ${safeCount} people, ${safePercentage}%`}
        >
          <div className="bar-value">
            <span className="bar-count">{safeCount}</span>
            <span className="bar-percentage">({safePercentage}%)</span>
          </div>
        </div>
      </div>

      <div className="bar-grade-english">{grade}</div>
    </div>
  )
}
