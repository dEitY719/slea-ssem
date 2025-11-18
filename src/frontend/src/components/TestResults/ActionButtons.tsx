// REQ: REQ-F-B4-1, REQ-F-B4-7
import React from 'react'
import { HomeIcon, ArrowPathIcon, DocumentTextIcon } from '@heroicons/react/24/outline'

interface ActionButtonsProps {
  onGoHome: () => void
  onRetake: () => void
  onViewExplanations?: () => void // REQ: REQ-F-B4-7
}

/**
 * Action Buttons Component
 * Displays navigation buttons for home, retake, and explanations
 *
 * REQ: REQ-F-B4-7 - Added "해설 보기" button
 */
export const ActionButtons: React.FC<ActionButtonsProps> = ({
  onGoHome,
  onRetake,
  onViewExplanations,
}) => {
  return (
    <div className="action-buttons">
      {/* REQ: REQ-F-B4-7 - View Explanations Button */}
      {onViewExplanations && (
        <button type="button" className="explanation-button" onClick={onViewExplanations}>
          <DocumentTextIcon className="button-icon" />
          문항별 해설 보기
        </button>
      )}

      <button type="button" className="primary-button" onClick={onGoHome}>
        <HomeIcon className="button-icon" />
        홈화면으로 이동
      </button>
      <button type="button" className="secondary-button" onClick={onRetake}>
        <ArrowPathIcon className="button-icon" />
        재응시하기
      </button>
    </div>
  )
}
