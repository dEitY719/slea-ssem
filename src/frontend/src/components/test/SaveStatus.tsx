// SaveStatus component for autosave feedback
// REQ: REQ-F-B2-6

import React from 'react'
import { ArrowPathIcon, CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
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
          <ArrowPathIcon className="save-icon" />
          <span className="save-text">저장 중...</span>
        </>
      )}
      {status === 'saved' && (
        <>
          <CheckCircleIcon className="save-icon" />
          <span className="save-text">저장됨</span>
        </>
      )}
      {status === 'error' && (
        <>
          <ExclamationTriangleIcon className="save-icon" />
          <span className="save-text">저장 실패</span>
        </>
      )}
    </div>
  )
}
