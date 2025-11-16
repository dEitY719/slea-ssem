// REQ: REQ-F-A2-2-2
import React, { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { submitProfileSurvey } from '../features/profile/profileSubmission'
import LevelSelector from '../components/LevelSelector'
import InfoBox, { InfoBoxIcons } from '../components/InfoBox'
import './SelfAssessmentPage.css'

/**
 * Self Assessment Page Component
 *
 * REQ: REQ-F-A2-2-2 - 자기평가 정보(수준) 입력
 * REQ: REQ-F-A2-2-3 - 필수 필드 입력 시 "완료" 버튼 활성화
 * REQ: REQ-F-A2-2-4 - "완료" 버튼 클릭 시 user_profile 저장 및 리다이렉트
 *
 * Features:
 * - Level selection (shared LevelSelector component)
 * - Complete button (enabled when level is selected)
 * - API integration with LEVEL_MAPPING conversion
 *
 * Route: /self-assessment
 *
 * Shared Components:
 * - LevelSelector: Reused with REQ-F-A2-Signup-4
 * - LEVEL_MAPPING: Centralized level conversion
 * - InfoBox: Consistent info display
 */

const SelfAssessmentPage: React.FC = () => {
  const [level, setLevel] = useState<number | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const navigate = useNavigate()

  const handleLevelChange = useCallback((selectedLevel: number) => {
    setLevel(selectedLevel)
    setErrorMessage(null)
  }, [])

  const handleCompleteClick = useCallback(async () => {
    if (level === null || isSubmitting) {
      return
    }

    setIsSubmitting(true)
    setErrorMessage(null)

      try {
        const response = await submitProfileSurvey({ level })

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
  }, [level, isSubmitting, navigate])

  const isCompleteEnabled = level !== null && !isSubmitting

  return (
    <main className="self-assessment-page">
      <div className="self-assessment-container">
        <h1 className="page-title">자기평가 입력</h1>
        <p className="page-description">
          현재 본인의 기술 수준을 선택해주세요. 이 정보는 맞춤형 테스트 생성에 활용됩니다.
        </p>

        {/* Shared LevelSelector component (REQ-F-A2-Signup-4, REQ-F-A2-2-2) */}
        <LevelSelector
          value={level}
          onChange={handleLevelChange}
          disabled={isSubmitting}
          showTitle={false}
        />

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

        <InfoBox title="수준 선택 가이드" icon={InfoBoxIcons.check}>
          <ul className="info-list">
            <li>본인의 현재 기술 수준을 솔직하게 평가해주세요</li>
            <li>선택한 수준에 맞춰 테스트 난이도가 조정됩니다</li>
            <li>나중에 프로필 수정에서 변경할 수 있습니다</li>
          </ul>
        </InfoBox>
      </div>
    </main>
  )
}

export default SelfAssessmentPage
