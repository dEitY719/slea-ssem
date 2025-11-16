// REQ: REQ-F-A2-2
import React, { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useNicknameCheck } from '../hooks/useNicknameCheck'
import { profileService } from '../services'
import { setCachedNickname } from '../utils/nicknameCache'
import NicknameInputSection from '../components/NicknameInputSection'
import './NicknameSetupPage.css'

/**
 * Nickname Setup Page Component
 *
 * REQ: REQ-F-A2-2 - 닉네임 입력 필드와 "중복 확인" 버튼 제공
 *
 * Features:
 * - Nickname input section (shared component)
 * - Next button to navigate to self-assessment
 *
 * Route: /nickname-setup
 */
const NicknameSetupPage: React.FC = () => {
  const {
    nickname,
    setNickname,
    checkStatus,
    errorMessage,
    suggestions,
    checkNickname,
    setManualError,
  } = useNicknameCheck()
  const navigate = useNavigate()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleCheckClick = useCallback(() => {
    if (isSubmitting) return
    checkNickname()
  }, [checkNickname, isSubmitting])

  const handleNextClick = useCallback(async () => {
    if (isSubmitting || checkStatus !== 'available') {
      return
    }

    setIsSubmitting(true)
      try {
        await profileService.registerNickname(nickname)
        setCachedNickname(nickname)
        setIsSubmitting(false)
        navigate('/self-assessment', { replace: true })
    } catch (error) {
      const message =
        error instanceof Error ? error.message : '닉네임 등록에 실패했습니다.'
      setManualError(message)
      setIsSubmitting(false)
    }
  }, [checkStatus, isSubmitting, navigate, nickname, setManualError])

  const isNextEnabled = checkStatus === 'available'
  const isNextDisabled = !isNextEnabled || isSubmitting

  return (
    <main className="nickname-setup-page">
      <div className="nickname-setup-container">
        <h1 className="page-title">닉네임 설정</h1>
        <p className="page-description">
          사용할 닉네임을 입력하고 중복 확인을 해주세요.
        </p>

        <NicknameInputSection
          nickname={nickname}
          setNickname={setNickname}
          checkStatus={checkStatus}
          errorMessage={errorMessage}
          suggestions={suggestions}
          onCheckClick={handleCheckClick}
          disabled={isSubmitting}
          showInfoBox={true}
        />

        <div className="form-actions">
          <button
            type="button"
            className="next-button"
            onClick={handleNextClick}
            disabled={isNextDisabled}
          >
            {isSubmitting ? '저장 중...' : '다음'}
          </button>
        </div>
      </div>
    </main>
  )
}

export default NicknameSetupPage
