import React from 'react'
import NumberInput from './NumberInput'
import RadioButtonGrid, { type RadioButtonOption } from './RadioButtonGrid'
import TextAreaInput from './TextAreaInput'

/**
 * Career Info Section Component
 *
 * Reusable component for career information fields:
 * - Career (years): number input (0-50)
 * - Job role: radio button grid (3 columns)
 * - Duty: textarea with character counter
 *
 * Used in:
 * - CareerInfoPage (REQ-F-A2-2)
 * - ProfileEditPage (REQ-F-A2-Edit)
 * - SignupPage (REQ-F-A2-Signup-4)
 */

export interface CareerInfoData {
  career: number
  jobRole: string
  duty: string
}

export interface CareerInfoSectionProps {
  /**
   * Career value (years, 0-50)
   */
  career: number

  /**
   * Job role value (S, E, M, G, F)
   */
  jobRole: string

  /**
   * Duty/responsibility description
   */
  duty: string

  /**
   * Callback when career value changes
   */
  onCareerChange: (value: number) => void

  /**
   * Callback when job role changes
   */
  onJobRoleChange: (value: string) => void

  /**
   * Callback when duty changes
   */
  onDutyChange: (value: string) => void

  /**
   * Whether fields are disabled (e.g., during form submission)
   */
  disabled?: boolean

  /**
   * Whether to show section title
   * @default false
   */
  showTitle?: boolean
}

// Radio button grid options for Job Role field (abbreviations only)
const JOB_ROLE_OPTIONS: RadioButtonOption[] = [
  { value: 'S', label: 'S' },
  { value: 'E', label: 'E' },
  { value: 'M', label: 'M' },
  { value: 'G', label: 'G' },
  { value: 'F', label: 'F' },
]

const CareerInfoSection: React.FC<CareerInfoSectionProps> = ({
  career,
  jobRole,
  duty,
  onCareerChange,
  onJobRoleChange,
  onDutyChange,
  disabled = false,
  showTitle = false,
}) => {
  return (
    <>
      {showTitle && <h2 className="section-title">경력 정보</h2>}

      {/* 경력(연차) - 숫자 입력 */}
      <NumberInput
        id="career"
        label="경력(연차)"
        value={career}
        onChange={onCareerChange}
        min={0}
        max={50}
        disabled={disabled}
        placeholder="0"
      />

      {/* 직군 - 라디오버튼 그리드 (3열) */}
      <RadioButtonGrid
        name="jobRole"
        legend="직군"
        options={JOB_ROLE_OPTIONS}
        value={jobRole}
        onChange={onJobRoleChange}
        disabled={disabled}
      />

      {/* 담당 업무 - 텍스트 입력 */}
      <TextAreaInput
        id="duty"
        label="담당 업무"
        value={duty}
        onChange={onDutyChange}
        disabled={disabled}
        maxLength={500}
        placeholder="담당하고 있는 주요 업무를 입력해주세요"
        rows={3}
      />
    </>
  )
}

export default CareerInfoSection
