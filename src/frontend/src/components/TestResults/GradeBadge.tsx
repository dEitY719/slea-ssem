// REQ: REQ-F-B4-1, REQ-F-B4-2
import React from 'react'
import { TrophyIcon } from '@heroicons/react/24/solid'
import { getGradeKorean, getGradeClass, isEliteGrade } from '../../utils/gradeHelpers'
import { SpecialBadge } from './SpecialBadge'

interface GradeBadgeProps {
  grade: string
}

/**
 * Grade Badge Component
 *
 * REQ: REQ-F-B4-1 - Displays the user's grade with color-coded styling
 * REQ: REQ-F-B4-2 - Displays special badge for Elite grade users
 */
export const GradeBadge: React.FC<GradeBadgeProps> = ({ grade }) => {
  const showSpecialBadge = isEliteGrade(grade)

  return (
    <div className="grade-badge-container">
      <div className={`grade-badge ${getGradeClass(grade)}`}>
        <TrophyIcon className="grade-icon" />
        <div className="grade-info">
          <p className="grade-label">등급</p>
          <p className="grade-value">{getGradeKorean(grade)}</p>
          <p className="grade-english">{grade}</p>
        </div>
      </div>

      {/* REQ: REQ-F-B4-2 - Special badge for Elite grade */}
      {showSpecialBadge && (
        <div className="special-badges-container">
          <SpecialBadge badgeType="Agent Specialist" />
        </div>
      )}
    </div>
  )
}
