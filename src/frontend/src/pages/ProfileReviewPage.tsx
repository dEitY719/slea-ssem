// REQ: REQ-F-A2-2-4
import React, { useCallback, useEffect, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { PencilIcon, PlayIcon } from '@heroicons/react/24/outline'
import { profileService } from '../services'
import InfoBox, { InfoBoxIcons } from '../components/InfoBox'
import './ProfileReviewPage.css'

/**
 * Profile Review Page Component
 *
 * REQ: REQ-F-A2-2-4 - "완료" 버튼 클릭 시 프로필 리뷰 페이지로 리다이렉트
 *
 * Features:
 * - Display user's nickname (fetched from API)
 * - Display self-assessment level (passed via navigation state)
 * - "시작하기" button to proceed to home
 * - "수정하기" button to go back to self-assessment
 *
 * Route: /profile-review
 */

type LocationState = {
  level?: number
  surveyId?: string
}

type NicknameResponse = {
  user_id: string
  nickname: string | null
  registered_at: string | null
  updated_at: string | null
}

/**
 * Convert level number to Korean text
 * @param level - Level number (1-5)
 * @returns Korean text representation
 */
const getLevelText = (level: number | undefined): string => {
  if (!level) return '정보 없음'
  if (level === 1) return '입문'
  if (level === 2) return '초급'
  if (level === 3) return '중급'
  if (level === 4) return '고급'
  if (level === 5) return '전문가'
  return '정보 없음'
}

const ProfileReviewPage: React.FC = () => {
  const [nickname, setNickname] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as LocationState

  useEffect(() => {
    const fetchNickname = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const response = await profileService.getNickname()
        setNickname(response.nickname)
      } catch (err) {
        const message =
          err instanceof Error ? err.message : '닉네임 정보를 불러오는데 실패했습니다.'
        setError(message)
      } finally {
        setIsLoading(false)
      }
    }

    fetchNickname()
  }, [])

  const handleStartClick = useCallback(() => {
    // Try to get surveyId from state (new test) or localStorage (retake)
    let surveyId = state?.surveyId

    if (!surveyId) {
      // REQ-F-B5-3: For retake, use saved surveyId from localStorage
      const savedSurveyId = localStorage.getItem('lastSurveyId')
      if (savedSurveyId) {
        surveyId = savedSurveyId
      } else {
        setError('자기평가 정보가 없습니다. 다시 시도해주세요.')
        return
      }
    } else {
      // Save surveyId to localStorage for future retakes (REQ-F-B5-3)
      localStorage.setItem('lastSurveyId', surveyId)
    }

    // Navigate to test page with surveyId
    navigate('/test', {
      state: {
        surveyId: surveyId,
        round: 1,
      },
    })
  }, [state?.surveyId, navigate])

  const handleEditClick = useCallback(() => {
    navigate('/self-assessment')
  }, [navigate])

  if (isLoading) {
    return (
      <main className="profile-review-page">
        <div className="profile-review-container">
          <p className="loading-message">로딩 중...</p>
        </div>
      </main>
    )
  }

  if (error) {
    return (
      <main className="profile-review-page">
        <div className="profile-review-container">
          <p className="error-message">{error}</p>
        </div>
      </main>
    )
  }

  return (
    <main className="profile-review-page">
      <div className="profile-review-container">
        <h1 className="page-title">프로필 확인</h1>
        <p className="page-description">
          입력하신 정보를 확인해주세요. 수정이 필요하면 "수정하기"를 클릭하세요.
        </p>

        <div className="profile-summary">
          <div className="profile-item">
            <span className="profile-label">닉네임</span>
            <span className="profile-value">{nickname || '정보 없음'}</span>
          </div>

          <div className="profile-item">
            <span className="profile-label">기술 수준</span>
            <span className="profile-value">{getLevelText(state?.level)}</span>
          </div>
        </div>

        <div className="button-group">
          <button
            type="button"
            className="edit-button"
            onClick={handleEditClick}
          >
            <PencilIcon className="button-icon" />
            수정하기
          </button>
          <button
            type="button"
            className="start-button"
            onClick={handleStartClick}
          >
            <PlayIcon className="button-icon" />
            테스트 시작
          </button>
        </div>

        <InfoBox title="다음 단계" icon={InfoBoxIcons.arrowRight}>
          <p className="info-text">
            "테스트 시작"을 클릭하면 AI 역량 레벨 테스트가 시작됩니다.
            1차 문제 5개가 생성되며, 약 10분이 소요됩니다.
          </p>
        </InfoBox>
      </div>
    </main>
  )
}

export default ProfileReviewPage
