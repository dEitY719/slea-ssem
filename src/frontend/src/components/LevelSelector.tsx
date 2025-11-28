/**
 * Level Selector Component
 *
 * Shared across:
 * - SignupPage (REQ-F-A2-Signup-4)
 * - ProfileSetupPage (REQ-F-A2-2-2)
 * - ProfileEditPage (future)
 *
 * Features:
 * - 5 level options (1-5) as radio buttons
 * - Visual selection feedback
 * - Level descriptions
 */

import React, { useCallback } from 'react'
import { LEVEL_OPTIONS, type LevelOption } from '../constants/profileLevels'
import './LevelSelector.css'

export interface LevelSelectorProps {
  value: number | null
  onChange: (level: number) => void
  disabled?: boolean
  showTitle?: boolean
}

const LevelSelector: React.FC<LevelSelectorProps> = ({
  value,
  onChange,
  disabled = false,
}) => {
  const handleChange = useCallback(
    (selectedLevel: number) => {
      if (!disabled) {
        onChange(selectedLevel)
      }
    },
    [onChange, disabled]
  )

  return (
    <section className="level-selector">
      <div className="form-group">
        <label className="form-label">기술 수준</label>
        <div className="level-options">
          {LEVEL_OPTIONS.map((option: LevelOption) => (
            <label
              key={option.value}
              className={`level-option ${value === option.value ? 'selected' : ''} ${disabled ? 'disabled' : ''}`}
            >
              <input
                type="radio"
                name="level"
                value={option.value}
                checked={value === option.value}
                onChange={() => handleChange(option.value)}
                disabled={disabled}
                aria-label={option.label}
              />
              <div className="level-content">
                <div className="level-label">{option.label}</div>
                <div className="level-description">{option.description}</div>
              </div>
            </label>
          ))}
        </div>
      </div>
    </section>
  )
}

export default LevelSelector
