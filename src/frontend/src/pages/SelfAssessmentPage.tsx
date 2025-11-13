// REQ: REQ-F-A2-2-2
import React, { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { profileService } from '../services'
import './SelfAssessmentPage.css'

/**
 * Self Assessment Page Component
 *
 * REQ: REQ-F-A2-2-2 - 자기평가 정보(수준) 입력
 * REQ: REQ-F-A2-2-3 - 필수 필드 입력 시 "완료" 버튼 활성화
 * REQ: REQ-F-A2-2-4 - "완료" 버튼 클릭 시 user_profile 저장 및 리다이렉트
 *
 * Features:
 * - Level selection (1-5 with radio buttons)
 * - Level descriptions for each option
 * - Complete button (enabled when level is selected)
 * - API integration with backend format conversion
 *
 * Route: /self-assessment
 */

type LevelOption = {
  value: number
  label: string
  description: string
}

const LEVEL_OPTIONS: LevelOption[] = [
  { value: 1, label: '1 - 입문', description: '기초 개념 학습 중' },
  { value: 2, label: '2 - 초급', description: '기본 업무 수행 가능' },
  { value: 3, label: '3 - 중급', description: '독립적으로 업무 수행' },
  { value: 4, label: '4 - 고급', description: '복잡한 문제 해결 가능' },
  { value: 5, label: '5 - 전문가', description: '다른 사람을 지도 가능' },
]

/**
 * Convert frontend level (1-5) to backend format
 * @param level - Frontend level (1-5)
 * @returns Backend level string ('beginner' | 'intermediate' | 'advanced')
 */
const convertLevelToBackend = (level: number): string => {
  if (level === 1) return 'beginner'
  if (level === 2 || level === 3) return 'intermediate'
  if (level === 4 || level === 5) return 'advanced'
  throw new Error(`Invalid level: ${level}`)
}

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
      const backendLevel = convertLevelToBackend(level)
      const response = await profileService.updateSurvey({
        level: backendLevel,
        career: 0,
        interests: [],
      })

      setIsSubmitting(false)
      navigate('/profile-review', {
        replace: true,
        state: { level, surveyId: response.survey_id },
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

        <div className="form-group">
          <label className="form-label">기술 수준</label>
          <div className="level-options">
            {LEVEL_OPTIONS.map((option) => (
              <label
                key={option.value}
                className={`level-option ${level === option.value ? 'selected' : ''}`}
              >
                <input
                  type="radio"
                  name="level"
                  value={option.value}
                  checked={level === option.value}
                  onChange={() => handleLevelChange(option.value)}
                  disabled={isSubmitting}
                  aria-label={option.label}
                />
                <div className="level-content">
                  <div className="level-label">{option.label}</div>
                  <div className="level-description">{option.description}</div>
                </div>
              </label>
            ))}
          </div>

          {errorMessage && <p className="error-message">{errorMessage}</p>}
        </div>

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

        <div className="info-box">
          <p className="info-title">수준 선택 가이드</p>
          <ul className="info-list">
            <li>본인의 현재 기술 수준을 솔직하게 평가해주세요</li>
            <li>선택한 수준에 맞춰 테스트 난이도가 조정됩니다</li>
            <li>나중에 프로필 수정에서 변경할 수 있습니다</li>
          </ul>
        </div>
      </div>
    </main>
  )
}

export default SelfAssessmentPage
