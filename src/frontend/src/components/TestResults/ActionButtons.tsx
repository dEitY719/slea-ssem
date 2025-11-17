// REQ: REQ-F-B4-1
import React from 'react'
import { HomeIcon, ArrowPathIcon } from '@heroicons/react/24/outline'

interface ActionButtonsProps {
  onGoHome: () => void
  onRetake: () => void
}

/**
 * Action Buttons Component
 * Displays navigation buttons for home and retake actions
 */
export const ActionButtons: React.FC<ActionButtonsProps> = ({ onGoHome, onRetake }) => {
  return (
    <div className="action-buttons">
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
