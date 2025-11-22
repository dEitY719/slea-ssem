// REQ: REQ-F-A2-2, REQ-F-B5-Retake-1
import React, { useCallback, useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { PageLayout } from '../components'
import NumberInput from '../components/NumberInput'
import RadioButtonGrid, { type RadioButtonOption } from '../components/RadioButtonGrid'
import TextAreaInput from '../components/TextAreaInput'
import InfoBox, { InfoBoxIcons } from '../components/InfoBox'
import './CareerInfoPage.css'

/**
 * Career Info Page Component
 *
 * REQ: REQ-F-A2-2 - 경력 정보 입력 (프로필 설정 1/2)
 *
 * Features:
 * - Career (years): number input (0-50)
 * - Job role: radio button grid (3 columns)
 * - Duty: textarea with character counter
 * - Data temporarily saved to localStorage
 *
 * Route: /career-info
 *
 * Flow: /set-nickname → /career-info → /self-assessment
 *
 * Shared Components:
 * - NumberInput: Reusable number input field
 * - RadioButtonGrid: Reusable radio button grid (3 columns per row)
 * - TextAreaInput: Reusable textarea with character counter
 * - InfoBox: Consistent info display
 */

const CAREER_TEMP_STORAGE_KEY = 'slea_ssem_career_temp'

// Radio button grid options for Job Role field (abbreviations only)
const JOB_ROLE_OPTIONS: RadioButtonOption[] = [
  { value: 'S', label: 'S' },
  { value: 'E', label: 'E' },
  { value: 'M', label: 'M' },
  { value: 'G', label: 'G' },
  { value: 'F', label: 'F' },
]

export interface CareerTempData {
  career: number
  jobRole: string
  duty: string
}

/**
 * Location state for retake mode - REQ: REQ-F-B5-Retake-1
 */
type LocationState = {
  retakeMode?: boolean
  profileData?: {
    surveyId: string
    level: string
    career: number
    jobRole: string
    duty: string
    interests: string[]
  }
}

const CareerInfoPage: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as LocationState | null

  const [career, setCareer] = useState<number>(0)
  const [jobRole, setJobRole] = useState<string>('')
  const [duty, setDuty] = useState<string>('')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // REQ-F-B5-Retake-1: Auto-fill form data when in retake mode
  useEffect(() => {
    if (state?.retakeMode && state?.profileData) {
      console.log('[CareerInfo] Retake mode detected, auto-filling form:', state.profileData)
      setCareer(state.profileData.career)
      setJobRole(state.profileData.jobRole)
      setDuty(state.profileData.duty)
    }
  }, [state])

  const handleCareerChange = useCallback((value: number) => {
    setCareer(value)
    setErrorMessage(null)
  }, [])

  const handleJobRoleChange = useCallback((value: string) => {
    setJobRole(value)
    setErrorMessage(null)
  }, [])

  const handleDutyChange = useCallback((value: string) => {
    setDuty(value)
    setErrorMessage(null)
  }, [])

  const handleNextClick = useCallback(() => {
    // Validate career range (0-50)
    if (career < 0 || career > 50) {
      setErrorMessage('경력은 0~50 사이의 값을 입력해주세요.')
      return
    }

    // Save data to localStorage
    const careerData: CareerTempData = {
      career,
      jobRole,
      duty,
    }
    localStorage.setItem(CAREER_TEMP_STORAGE_KEY, JSON.stringify(careerData))

    // REQ-F-B5-Retake-1: Pass profile data to next page if in retake mode
    if (state?.retakeMode && state?.profileData) {
      navigate('/self-assessment', {
        replace: true,
        state: {
          retakeMode: true,
          profileData: {
            ...state.profileData,
            // Update with potentially modified career info
            career,
            jobRole,
            duty,
          },
        },
      })
    } else {
      // Normal flow: navigate without state
      navigate('/self-assessment', { replace: true })
    }
  }, [career, jobRole, duty, navigate, state])

  return (
    <PageLayout mainClassName="career-info-page" containerClassName="career-info-container">
      <h1 className="page-title">경력 정보 입력</h1>
      <p className="page-description">
        현재 본인의 경력 정보를 입력해주세요. 모든 필드는 선택 사항입니다.
      </p>

      <div className="form-section">
        {/* 1. 경력(연차) - 숫자 입력 */}
        <NumberInput
          id="career"
          label="경력(연차)"
          value={career}
          onChange={handleCareerChange}
          min={0}
          max={50}
          placeholder="0"
        />

        {/* 2. 직군 - 라디오버튼 그리드 (3열) */}
        <RadioButtonGrid
          name="jobRole"
          legend="직군"
          options={JOB_ROLE_OPTIONS}
          value={jobRole}
          onChange={handleJobRoleChange}
        />

        {/* 3. 담당 업무 - 텍스트 입력 */}
        <TextAreaInput
          id="duty"
          label="담당 업무"
          value={duty}
          onChange={handleDutyChange}
          maxLength={500}
          placeholder="담당하고 있는 주요 업무를 입력해주세요"
          rows={3}
        />
      </div>

      {errorMessage && <p className="error-message">{errorMessage}</p>}

      <div className="form-actions">
        <button
          type="button"
          className="next-button"
          onClick={handleNextClick}
        >
          다음
        </button>
      </div>

      <InfoBox title="경력 정보 가이드" icon={InfoBoxIcons.check}>
        <ul className="info-list">
          <li>모든 필드는 선택 사항입니다</li>
          <li>경력은 0~50년 사이로 입력해주세요</li>
          <li>직군: S(Software), E(Engineering), M(Marketing), G(기획), F(Finance/인사)</li>
          <li>입력한 정보는 다음 단계에서 함께 저장됩니다</li>
        </ul>
      </InfoBox>
    </PageLayout>
  )
}

export default CareerInfoPage
export { CAREER_TEMP_STORAGE_KEY }
