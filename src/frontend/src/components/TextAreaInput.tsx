/**
 * TextArea Input Component
 *
 * Reusable textarea input field
 *
 * Shared across:
 * - SelfAssessmentPage (duty field)
 * - SignupPage (duty field)
 * - ProfileEditPage (duty field)
 */

import React from 'react'
import './TextAreaInput.css'

export interface TextAreaInputProps {
  id: string
  label: string
  value: string
  onChange: (value: string) => void
  disabled?: boolean
  placeholder?: string
  maxLength?: number
  rows?: number
}

const TextAreaInput: React.FC<TextAreaInputProps> = ({
  id,
  label,
  value,
  onChange,
  disabled = false,
  placeholder = '',
  maxLength = 500,
  rows = 3,
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value)
  }

  return (
    <div className="textarea-input-field">
      <label htmlFor={id} className="textarea-input-label">
        {label}
      </label>
      <textarea
        id={id}
        className="textarea-input"
        value={value}
        onChange={handleChange}
        disabled={disabled}
        placeholder={placeholder}
        maxLength={maxLength}
        rows={rows}
      />
      {maxLength && (
        <div className="textarea-counter">
          {value.length} / {maxLength}
        </div>
      )}
    </div>
  )
}

export default TextAreaInput
