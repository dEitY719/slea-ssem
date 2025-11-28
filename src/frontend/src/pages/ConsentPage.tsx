// REQ: REQ-F-A3-1, REQ-F-A3-2, REQ-F-A3-3, REQ-F-A3-4
import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline'
import { PageLayout } from '../components'
import { profileService } from '../services/profileService'
import { useUserProfile } from '../hooks/useUserProfile'
import './ConsentPage.css'

/**
 * Consent Page Component
 *
 * REQ: REQ-F-A3 - 개인정보 수집 및 이용 동의
 *
 * Features:
 * - REQ-F-A3-1: Display privacy consent modal/page
 * - REQ-F-A3-2: Show collection items, purpose, retention period
 * - REQ-F-A3-3: Proceed to next step only if user agrees
 * - REQ-F-A3-4: Return to home if user disagrees
 * - REQ-F-A3-5: Save consent status to DB
 *
 * Route: /consent
 */

type SurveyProgress = {
  surveyId: string | null
  level: number | null
}

const getSurveyProgress = (): SurveyProgress => {
  if (typeof window === 'undefined') {
    return { surveyId: null, level: null }
  }

  const surveyId = localStorage.getItem('lastSurveyId')
  const levelRaw = localStorage.getItem('lastSurveyLevel')

  return {
    surveyId,
    level: levelRaw ? Number(levelRaw) : null,
  }
}

const ConsentPage: React.FC = () => {
  const navigate = useNavigate()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { checkNickname } = useUserProfile()

  const handleAgree = async () => {
    setIsSubmitting(true)
    setError(null)

    try {
      // REQ: REQ-F-A3-5 - Save consent to DB
      await profileService.updateConsent(true)

      // REQ: REQ-F-A3-3 - Proceed to next step based on user status
      // Check nickname and profile status to determine the right page
      const currentNickname = await checkNickname()
      const { surveyId, level } = getSurveyProgress()

      if (currentNickname === null) {
        // User hasn't set nickname yet, redirect to nickname setup
        navigate('/nickname-setup')
      } else if (surveyId) {
        // User has nickname and completed profile, show review page
        navigate('/profile-review', {
          state: {
            surveyId,
            level: level ?? undefined,
          },
        })
      } else {
        // User has nickname but no profile yet, proceed to career info
        navigate('/career-info')
      }
    } catch (err) {
      console.error('Failed to save consent:', err)
      setError('동의 처리 중 오류가 발생했습니다. 다시 시도해주세요.')
      setIsSubmitting(false)
    }
  }

  const handleDisagree = () => {
    // REQ: REQ-F-A3-4 - Return to home without saving
    navigate('/home')
  }

  return (
    <PageLayout mainClassName="consent-page" containerClassName="consent-container">
      <h1 className="consent-title">개인정보 수집 및 이용 동의</h1>

        <div className="consent-content">
          {/* REQ: REQ-F-A3-2 - Collection items, purpose, retention period */}
          <section className="consent-section">
            <h2 className="section-heading">1. 수집 항목</h2>
            <p className="section-text">
              Learning Platform은 서비스 제공을 위해 다음 정보를 수집합니다:
            </p>
            <ul className="consent-list">
              <li>필수 항목: 닉네임, 자기평가 정보 (수준, 경력, 직군, 관심분야)</li>
              <li>서비스 이용 기록: 테스트 응답, 테스트 결과, 학습 이력</li>
            </ul>
          </section>

          <section className="consent-section">
            <h2 className="section-heading">2. 이용 목적</h2>
            <p className="section-text">
              수집된 개인정보는 다음의 목적으로 이용됩니다:
            </p>
            <ul className="consent-list">
              <li>개인 맞춤형 학습 콘텐츠 제공</li>
              <li>적응형 레벨 테스트 및 평가 제공</li>
              <li>학습 진행 상황 추적 및 분석</li>
              <li>전체 상대 순위 및 통계 산출</li>
              <li>서비스 개선 및 새로운 기능 개발</li>
            </ul>
          </section>

          <section className="consent-section">
            <h2 className="section-heading">3. 보유 및 이용 기간</h2>
            <p className="section-text">
              개인정보는 다음 기간 동안 보유 및 이용됩니다:
            </p>
            <ul className="consent-list">
              <li>
                <strong>원칙:</strong> 서비스 이용 기간 동안 보유
              </li>
              <li>
                <strong>예외:</strong> 법령에 따라 보존이 필요한 경우 해당 기간 동안 보유
              </li>
              <li>
                <strong>삭제 요청:</strong> 사용자가 삭제를 요청하는 경우 즉시 파기
              </li>
            </ul>
          </section>

          <section className="consent-section">
            <h2 className="section-heading">4. 동의 거부 권리</h2>
            <p className="section-text">
              귀하는 개인정보 수집 및 이용에 대한 동의를 거부할 권리가 있습니다.
              다만, 동의를 거부하시는 경우 서비스 이용이 제한될 수 있습니다.
            </p>
          </section>

          {error && (
            <div className="error-message">
              <XCircleIcon className="error-icon" />
              <span>{error}</span>
            </div>
          )}
        </div>

        <div className="consent-actions">
          <button
            type="button"
            className="disagree-button"
            onClick={handleDisagree}
            disabled={isSubmitting}
          >
            <XCircleIcon className="button-icon" />
            동의하지 않음
          </button>

          <button
            type="button"
            className="agree-button"
            onClick={handleAgree}
            disabled={isSubmitting}
          >
            <CheckCircleIcon className="button-icon" />
            {isSubmitting ? '처리 중...' : '동의함'}
          </button>
        </div>

        <p className="consent-footer">
          위 내용을 확인하였으며, 개인정보 수집 및 이용에 동의합니다.
        </p>
    </PageLayout>
  )
}

export default ConsentPage
