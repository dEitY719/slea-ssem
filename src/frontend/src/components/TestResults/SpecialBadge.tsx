// REQ: REQ-F-B4-2
import React from 'react'
import { SparklesIcon } from '@heroicons/react/24/solid'

export type SpecialBadgeType = 'Agent Specialist'

interface SpecialBadgeProps {
  badgeType: SpecialBadgeType
}

/**
 * Special Badge Component
 *
 * REQ: REQ-F-B4-2 - Elite 등급 사용자에게 특수 배지 표시
 *
 * Displays special achievement badges for Elite grade users.
 * Currently supports "Agent Specialist" badge.
 */
export const SpecialBadge: React.FC<SpecialBadgeProps> = ({ badgeType }) => {
  return (
    <div className="special-badge">
      <SparklesIcon className="special-badge-icon" />
      <span className="special-badge-text">{badgeType}</span>
    </div>
  )
}
