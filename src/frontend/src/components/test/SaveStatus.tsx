// SaveStatus component for autosave feedback
// REQ: REQ-F-B2-6

import React from 'react'
import './SaveStatus.css'

export type SaveStatusType = 'idle' | 'saving' | 'saved' | 'error'

interface SaveStatusProps {
  status: SaveStatusType
}

/**
 * SaveStatus Component
 *
 * Displays autosave status with visual feedback
 */
export const SaveStatus: React.FC<SaveStatusProps> = ({ status }) => {
  if (status === 'idle') {
    return null
  }

  return (
    <div className={`save-status save-status-${status}`}>
      {status === 'saving' && (
        <>
          <span className="save-icon">💾</span>
          <span className="save-text">저장 중...</span>
        </>
      )}
      {status === 'saved' && (
        <>
          <span className="save-icon">✓</span>
          <span className="save-text">저장됨</span>
        </>
      )}
      {status === 'error' && (
        <>
          <span className="save-icon">⚠</span>
          <span className="save-text">저장 실패</span>
        </>
      )}
    </div>
  )
}
