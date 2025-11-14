// REQ: REQ-F-B4-1
import React from 'react'
import { TrophyIcon } from '@heroicons/react/24/solid'
import { getGradeKorean, getGradeClass } from '../../utils/gradeHelpers'

interface GradeBadgeProps {
  grade: string
}

/**
 * Grade Badge Component
 * Displays the user's grade with color-coded styling
 */
export const GradeBadge: React.FC<GradeBadgeProps> = ({ grade }) => {
  return (
    <div className={`grade-badge ${getGradeClass(grade)}`}>
      <TrophyIcon className="grade-icon" />
      <div className="grade-info">
        <p className="grade-label">등급</p>
        <p className="grade-value">{getGradeKorean(grade)}</p>
        <p className="grade-english">{grade}</p>
      </div>
    </div>
  )
}
