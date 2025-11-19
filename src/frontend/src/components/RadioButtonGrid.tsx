/**
 * Radio Button Grid Component
 *
 * Reusable radio button grid with 3 columns per row
 *
 * Shared across:
 * - SelfAssessmentPage (job role, interests)
 * - SignupPage (job role, interests)
 * - ProfileEditPage (job role, interests)
 */

import React from 'react'
import './RadioButtonGrid.css'

export interface RadioButtonOption {
  value: string
  label: string
}

export interface RadioButtonGridProps {
  name: string
  legend: string
  options: RadioButtonOption[]
  value: string
  onChange: (value: string) => void
  disabled?: boolean
}

const RadioButtonGrid: React.FC<RadioButtonGridProps> = ({
  name,
  legend,
  options,
  value,
  onChange,
  disabled = false,
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!disabled) {
      onChange(e.target.value)
    }
  }

  return (
    <div className="radio-button-grid-field">
      <fieldset className="radio-button-fieldset">
        <legend className="radio-button-legend">{legend}</legend>
        <div className="radio-button-grid">
          {options.map((option) => (
            <label
              key={option.value}
              className={`radio-button-item ${value === option.value ? 'selected' : ''} ${disabled ? 'disabled' : ''}`}
            >
              <input
                type="radio"
                name={name}
                value={option.value}
                checked={value === option.value}
                onChange={handleChange}
                disabled={disabled}
                aria-label={option.label}
              />
              <span className="radio-button-label">{option.label}</span>
            </label>
          ))}
        </div>
      </fieldset>
    </div>
  )
}

export default RadioButtonGrid
