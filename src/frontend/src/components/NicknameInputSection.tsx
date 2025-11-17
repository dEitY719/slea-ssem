/**
 * Nickname Input Section Component
 *
 * Shared across:
 * - NicknameSetupPage (REQ-F-A2)
 * - SignupPage (REQ-F-A2-Signup-3)
 *
 * Features:
 * - Nickname input field (3-30 characters)
 * - Duplicate check button
 * - Real-time validation
 * - Status message display (success/error)
 * - Suggestions on duplicate (up to 3)
 * - InfoBox with nickname rules
 */

import React, { useCallback, useMemo } from 'react'
import InfoBox from './InfoBox'
import './NicknameInputSection.css'

export type NicknameCheckStatus = 'idle' | 'checking' | 'available' | 'taken' | 'error'

export interface NicknameInputSectionProps {
  nickname: string
  setNickname: (nickname: string) => void
  checkStatus: NicknameCheckStatus
  errorMessage: string | null
  suggestions: string[]
  onCheckClick: () => void
  disabled?: boolean
  showInfoBox?: boolean
}

/**
 * Hook to generate status message based on checkStatus
 * Extracted from NicknameSetupPage and SignupPage
 */
export const useNicknameStatusMessage = (
  checkStatus: NicknameCheckStatus,
  errorMessage: string | null
) => {
  return useMemo(() => {
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
  }, [checkStatus, errorMessage])
}

const NicknameInputSection: React.FC<NicknameInputSectionProps> = ({
  nickname,
  setNickname,
  checkStatus,
  errorMessage,
  suggestions,
  onCheckClick,
  disabled = false,
  showInfoBox = true,
}) => {
  const statusMessage = useNicknameStatusMessage(checkStatus, errorMessage)
  const isChecking = checkStatus === 'checking'
  const isInputDisabled = isChecking || disabled
  const isCheckButtonDisabled = isInputDisabled || nickname.length === 0

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setNickname(e.target.value)
    },
    [setNickname]
  )

  const handleSuggestionClick = useCallback(
    (suggestion: string) => {
      setNickname(suggestion)
    },
    [setNickname]
  )

  return (
    <section className="nickname-input-section">
      <h2 className="section-title">닉네임 설정</h2>

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
            onChange={handleInputChange}
            placeholder="영문자, 숫자, 언더스코어 (3-30자)"
            maxLength={30}
            disabled={isInputDisabled}
          />
          <button
            className="check-button"
            onClick={onCheckClick}
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
                    onClick={() => handleSuggestionClick(suggestion)}
                  >
                    {suggestion}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {showInfoBox && (
        <InfoBox title="닉네임 규칙">
          <ul className="info-list">
            <li>3-30자 사이로 입력해주세요</li>
            <li>영문자, 숫자, 언더스코어(_)만 사용 가능합니다</li>
            <li>금칙어는 사용할 수 없습니다</li>
          </ul>
        </InfoBox>
      )}
    </section>
  )
}

export default NicknameInputSection
