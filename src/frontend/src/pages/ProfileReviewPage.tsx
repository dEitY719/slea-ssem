// REQ: REQ-F-A2-2-4
import React, { useCallback, useEffect, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { transport } from '../lib/transport'
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
        const response = await transport.get<NicknameResponse>('/profile/nickname')
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
    navigate('/home', { replace: true })
  }, [navigate])

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
            수정하기
          </button>
          <button
            type="button"
            className="start-button"
            onClick={handleStartClick}
          >
            시작하기
          </button>
        </div>

        <div className="info-box">
          <p className="info-title">다음 단계</p>
          <p className="info-text">
            "시작하기"를 클릭하면 홈 화면으로 이동합니다.
            테스트를 시작하거나 대시보드를 확인할 수 있습니다.
          </p>
        </div>
      </div>
    </main>
  )
}

export default ProfileReviewPage
