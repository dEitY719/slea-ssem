// REQ: REQ-F-A2-2, REQ-F-B5-Retake-1
import React, { useCallback, useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { PageLayout } from '../components'
import CareerInfoSection from '../components/CareerInfoSection'
import InfoBox, { InfoBoxIcons } from '../components/InfoBox'
import { type RetakeLocationState } from '../types/profile'
import { debugLog } from '../utils/logger'
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

export interface CareerTempData {
  career: number
  jobRole: string
  duty: string
}

const CareerInfoPage: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as RetakeLocationState | null

  const [career, setCareer] = useState<number>(0)
  const [jobRole, setJobRole] = useState<string>('')
  const [duty, setDuty] = useState<string>('')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // REQ-F-B5-Retake-1: Auto-fill form data when in retake mode
  useEffect(() => {
    if (state?.retakeMode && state?.profileData) {
      debugLog('[CareerInfo] Retake mode detected, auto-filling form:', state.profileData)
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
        <CareerInfoSection
          career={career}
          jobRole={jobRole}
          duty={duty}
          onCareerChange={handleCareerChange}
          onJobRoleChange={handleJobRoleChange}
          onDutyChange={handleDutyChange}
          showTitle={false}
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
