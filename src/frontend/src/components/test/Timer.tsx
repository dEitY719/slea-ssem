// Timer component for test page
// REQ: REQ-F-B2-2, REQ-F-B2-5

import React from 'react'
import { ClockIcon } from '@heroicons/react/24/outline'
import './Timer.css'

interface TimerProps {
  timeRemaining: number
}

/**
 * Get timer color based on remaining time (REQ-F-B2-5)
 * @param seconds - Remaining time in seconds
 * @returns Color string ('green' | 'orange' | 'red')
 */
const getTimerColor = (seconds: number): string => {
  if (seconds > 15 * 60) return 'green'   // 16+ minutes
  if (seconds > 5 * 60) return 'orange'   // 6-15 minutes
  return 'red'                             // 5 minutes or less
}

/**
 * Format time as MM:SS (REQ-F-B2-2)
 * @param seconds - Time in seconds
 * @returns Formatted time string (e.g., "20:00")
 */
const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

/**
 * Timer Component
 *
 * Displays countdown timer with color transitions
 */
export const Timer: React.FC<TimerProps> = ({ timeRemaining }) => {
  const color = getTimerColor(timeRemaining)
  const formattedTime = formatTime(timeRemaining)

  return (
    <div className={`timer timer-${color}`}>
      <ClockIcon className="timer-icon" />
      <span className="timer-text">{formattedTime}</span>
    </div>
  )
}
