// REQ: REQ-F-A2-2
import React, { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useNicknameCheck } from '../hooks/useNicknameCheck'
import { transport } from '../lib/transport'
import './NicknameSetupPage.css'

/**
 * Nickname Setup Page Component
 *
 * REQ: REQ-F-A2-2 - 닉네임 입력 필드와 "중복 확인" 버튼 제공
 *
 * Features:
 * - Nickname input field (3-30 characters)
 * - Duplicate check button
 * - Real-time validation
 * - Availability status display
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
      await transport.post('/profile/register', { nickname })
      setIsSubmitting(false)
      navigate('/self-assessment', { replace: true })
    } catch (error) {
      const message =
        error instanceof Error ? error.message : '닉네임 등록에 실패했습니다.'
      setManualError(message)
      setIsSubmitting(false)
    }
  }, [checkStatus, isSubmitting, navigate, nickname, setManualError])

  const getStatusMessage = () => {
    if (checkStatus === 'available') {
      return {
        text: '사용 가능한 닉네임입니다.',
        className: 'status-message success',
      }
    }
    if (checkStatus === 'taken') {
      return {
        text: '이미 사용 중인 닉네임입니다.',
        className: 'status-message error',
      }
    }
    if (checkStatus === 'error' && errorMessage) {
      return {
        text: errorMessage,
        className: 'status-message error',
      }
    }
    return null
  }

  const statusMessage = getStatusMessage()
  const isChecking = checkStatus === 'checking'
  const isNextEnabled = checkStatus === 'available'
  const isInputDisabled = isChecking || isSubmitting
  const isCheckButtonDisabled = isInputDisabled || nickname.length === 0
  const isNextDisabled = !isNextEnabled || isInputDisabled

  return (
    <main className="nickname-setup-page">
      <div className="nickname-setup-container">
        <h1 className="page-title">닉네임 설정</h1>
        <p className="page-description">
          사용할 닉네임을 입력하고 중복 확인을 해주세요.
        </p>

        <div className="form-group">
          <label htmlFor="nickname-input" className="form-label">
            닉네임
          </label>
          <div className="input-group">
            <input
              id="nickname-input"
              type="text"
              className="nickname-input"
              value={nickname}
              onChange={(e) => setNickname(e.target.value)}
              placeholder="영문자, 숫자, 언더스코어 (3-30자)"
              maxLength={30}
              disabled={isInputDisabled}
            />
            <button
              className="check-button"
              onClick={handleCheckClick}
              disabled={isCheckButtonDisabled}
            >
              {isChecking ? '확인 중...' : '중복 확인'}
            </button>
          </div>

          {statusMessage && (
            <p className={statusMessage.className}>{statusMessage.text}</p>
          )}

          {checkStatus === 'taken' && suggestions.length > 0 && (
            <div className="suggestions">
              <p className="suggestions-title">추천 닉네임:</p>
              <ul className="suggestions-list">
                {suggestions.map((suggestion) => (
                  <li key={suggestion}>
                    <button
                      className="suggestion-button"
                      onClick={() => setNickname(suggestion)}
                    >
                      {suggestion}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

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

        <div className="info-box">
          <p className="info-title">닉네임 규칙</p>
          <ul className="info-list">
            <li>3-30자 사이로 입력해주세요</li>
            <li>영문자, 숫자, 언더스코어(_)만 사용 가능합니다</li>
            <li>금칙어는 사용할 수 없습니다</li>
          </ul>
        </div>
      </div>
    </main>
  )
}

export default NicknameSetupPage
