// REQ: REQ-F-A1-2
import React from 'react'
import './LoadingSpinner.css'

interface LoadingSpinnerProps {
  message?: string
}

/**
 * Loading spinner component with optional message
 *
 * @param message - Optional loading message to display (default: "로딩 중입니다...")
 */
export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = '로딩 중입니다...',
}) => {
  return (
    <div className="loading-container">
      <div className="loading-spinner" />
      <p className="loading-text">{message}</p>
    </div>
  )
}
