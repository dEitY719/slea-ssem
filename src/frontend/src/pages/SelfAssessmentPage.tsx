// REQ: REQ-F-A2-3, REQ-F-B5-Retake-1, REQ-F-B5-Retake-2
import React, { useCallback, useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { PageLayout } from '../components'
import { submitProfileSurvey } from '../features/profile/profileSubmission'
import LevelSelector from '../components/LevelSelector'
import RadioButtonGrid, { type RadioButtonOption } from '../components/RadioButtonGrid'
import InfoBox, { InfoBoxIcons } from '../components/InfoBox'
import { CAREER_TEMP_STORAGE_KEY, type CareerTempData } from './CareerInfoPage'
import './SelfAssessmentPage.css'

/**
 * Self Assessment Page Component
 *
 * REQ: REQ-F-A2-3 - 관심분야 및 기술 수준 입력 (프로필 설정 2/2)
 *
 * Features:
 * - Interests selection: radio button grid (3 columns)
 * - Level selection: slider (1-5, required)
 * - Loads career data from localStorage (from CareerInfoPage)
 * - Complete button (enabled when level is selected)
 * - Combines career data + interests/level and submits to API
 *
 * Route: /self-assessment
 *
 * Flow: /career-info → /self-assessment → /profile-review
 *
 * Shared Components:
 * - LevelSelector: Reusable level selector (1-5)
 * - RadioButtonGrid: Reusable radio button grid (3 columns per row)
 * - InfoBox: Consistent info display
 */

// Radio button grid options for Interests field
const INTERESTS_OPTIONS: RadioButtonOption[] = [
  { value: 'AI', label: 'AI' },
  { value: 'ML', label: 'ML' },
  { value: 'Backend', label: 'Backend' },
  { value: 'Frontend', label: 'Frontend' },
]

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

const SelfAssessmentPage: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as LocationState | null

  const [level, setLevel] = useState<number | null>(null)
  const [interests, setInterests] = useState<string>('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // REQ-F-B5-Retake-1: Auto-fill form data when in retake mode
  useEffect(() => {
    if (state?.retakeMode && state?.profileData) {
      console.log('[SelfAssessment] Retake mode detected, auto-filling form:', state.profileData)

      // Convert level string to number for LevelSelector
      const levelMap: Record<string, number> = {
        'beginner': 1,
        'intermediate': 2,
        'inter-advanced': 3,
        'advanced': 4,
        'elite': 5,
      }
      const levelNum = levelMap[state.profileData.level] || null
      setLevel(levelNum)

      // Join interests array to comma-separated string
      setInterests(state.profileData.interests.join(', '))
    }
  }, [state])

  const handleLevelChange = useCallback((selectedLevel: number) => {
    setLevel(selectedLevel)
    setErrorMessage(null)
  }, [])

  const handleInterestsChange = useCallback((value: string) => {
    setInterests(value)
    setErrorMessage(null)
  }, [])

  const handleCompleteClick = useCallback(async () => {
    if (level === null || isSubmitting) {
      return
    }

    setIsSubmitting(true)
    setErrorMessage(null)

    try {
      // Load career data from localStorage
      const careerDataStr = localStorage.getItem(CAREER_TEMP_STORAGE_KEY)
      const careerData: CareerTempData = careerDataStr
        ? JSON.parse(careerDataStr)
        : { career: 0, jobRole: '', duty: '' }

      // Combine career data + interests/level
      const response = await submitProfileSurvey({
        level,
        career: careerData.career,
        jobRole: careerData.jobRole,
        duty: careerData.duty,
        interests,
      })

      // Clear temporary career data
      localStorage.removeItem(CAREER_TEMP_STORAGE_KEY)

      setIsSubmitting(false)
      navigate('/profile-review', {
        replace: true,
        state: { level, surveyId: response.surveyId },
      })
    } catch (error) {
      const message =
        error instanceof Error ? error.message : '자기평가 정보 저장에 실패했습니다.'
      setErrorMessage(message)
      setIsSubmitting(false)
    }
  }, [level, interests, isSubmitting, navigate])

  const isCompleteEnabled = level !== null && !isSubmitting

  return (
    <PageLayout mainClassName="self-assessment-page" containerClassName="self-assessment-container">
      <h1 className="page-title">관심분야 및 기술 수준 입력</h1>
        <p className="page-description">
          관심 있는 분야와 현재 본인의 기술 수준을 선택해주세요. 기술 수준은 필수 항목입니다.
        </p>

        <div className="form-section">
          {/* 1. 관심분야 - 라디오버튼 그리드 (3열) */}
          <RadioButtonGrid
            name="interests"
            legend="관심분야"
            options={INTERESTS_OPTIONS}
            value={interests}
            onChange={handleInterestsChange}
            disabled={isSubmitting}
          />

          {/* 2. 수준 (1-5 슬라이더) */}
          <LevelSelector
            value={level}
            onChange={handleLevelChange}
            disabled={isSubmitting}
            showTitle={true}
          />
        </div>

        {errorMessage && <p className="error-message">{errorMessage}</p>}

        <div className="form-actions">
          <button
            type="button"
            className="complete-button"
            onClick={handleCompleteClick}
            disabled={!isCompleteEnabled}
          >
            {isSubmitting ? '제출 중...' : '완료'}
          </button>
        </div>

        <InfoBox title="자기평가 가이드" icon={InfoBoxIcons.check}>
          <ul className="info-list">
            <li>관심분야는 선택 사항입니다</li>
            <li>기술 수준은 필수 항목입니다 (1~5 중 선택)</li>
            <li>선택한 수준에 맞춰 테스트 난이도가 조정됩니다</li>
            <li>본인의 현재 기술 수준을 솔직하게 평가해주세요</li>
            <li>나중에 프로필 수정에서 변경할 수 있습니다</li>
          </ul>
        </InfoBox>
    </PageLayout>
  )
}

export default SelfAssessmentPage
