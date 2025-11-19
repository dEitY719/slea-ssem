/**
 * Radio Group Component
 *
 * Reusable radio button group with options
 *
 * Shared across:
 * - SelfAssessmentPage (job role, interests)
 * - SignupPage (job role, interests)
 * - ProfileEditPage (job role, interests)
 */

import React from 'react'
import './RadioGroup.css'

export interface RadioOption {
  value: string
  label: string
}

export interface RadioGroupProps {
  name: string
  legend: string
  options: RadioOption[]
  value: string
  onChange: (value: string) => void
  disabled?: boolean
}

const RadioGroup: React.FC<RadioGroupProps> = ({
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
    <div className="radio-group-field">
      <fieldset className="radio-fieldset">
        <legend className="radio-legend">{legend}</legend>
        <div className="radio-options">
          {options.map((option) => (
            <label
              key={option.value}
              className={`radio-option ${value === option.value ? 'selected' : ''} ${disabled ? 'disabled' : ''}`}
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
              <span className="radio-label">{option.label}</span>
            </label>
          ))}
        </div>
      </fieldset>
    </div>
  )
}

export default RadioGroup
