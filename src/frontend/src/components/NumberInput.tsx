/**
 * Number Input Component
 *
 * Reusable number input field with validation
 *
 * Shared across:
 * - SelfAssessmentPage (career field)
 * - SignupPage (career field)
 * - ProfileEditPage (career field)
 */

import React from 'react'
import './NumberInput.css'

export interface NumberInputProps {
  id: string
  label: string
  value: number
  onChange: (value: number) => void
  min?: number
  max?: number
  disabled?: boolean
  placeholder?: string
}

const NumberInput: React.FC<NumberInputProps> = ({
  id,
  label,
  value,
  onChange,
  min = 0,
  max,
  disabled = false,
  placeholder = '0',
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value
    onChange(val === '' ? 0 : parseInt(val, 10))
  }

  return (
    <div className="number-input-field">
      <label htmlFor={id} className="number-input-label">
        {label}
      </label>
      <input
        id={id}
        type="number"
        className="number-input"
        value={value}
        onChange={handleChange}
        min={min}
        max={max}
        disabled={disabled}
        placeholder={placeholder}
      />
    </div>
  )
}

export default NumberInput
