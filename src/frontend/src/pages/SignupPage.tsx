// REQ: REQ-F-A2-Signup-3
import React, { useCallback, useMemo } from 'react'
import { useNicknameCheck } from '../hooks/useNicknameCheck'
import './SignupPage.css'

/**
 * Unified Signup Page Component
 *
 * REQ: REQ-F-A2-Signup-3 - 통합 회원가입 페이지에 닉네임 입력 섹션 표시
 *
 * Features:
 * - Nickname input section (REQ-F-A2-Signup-3)
 *   - Input field (3-30 characters)
 *   - Duplicate check button
 *   - Real-time validation
 *   - Suggestions on duplicate (up to 3)
 * - Profile input section (REQ-F-A2-Signup-4, to be implemented)
 * - Submit button (REQ-F-A2-Signup-5/6, to be implemented)
 *
 * Route: /signup
 */
const SignupPage: React.FC = () => {
  const {
    nickname,
    setNickname,
    checkStatus,
    errorMessage,
    suggestions,
    checkNickname,
  } = useNicknameCheck()

  const handleCheckClick = useCallback(() => {
    checkNickname()
  }, [checkNickname])

  // Memoize status message to avoid recalculation on every render
  const statusMessage = useMemo(() => {
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

  const isChecking = checkStatus === 'checking'
  const isCheckButtonDisabled = isChecking || nickname.length === 0

  return (
    <main className="signup-page">
      <div className="signup-container">
        <h1 className="page-title">회원가입</h1>
        <p className="page-description">
          닉네임과 자기평가 정보를 입력하여 가입을 완료하세요.
        </p>

        {/* REQ-F-A2-Signup-3: Nickname Section */}
        <section className="nickname-section">
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
                onChange={(e) => setNickname(e.target.value)}
                placeholder="영문자, 숫자, 언더스코어 (3-30자)"
                maxLength={30}
                disabled={isChecking}
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

          <div className="info-box">
            <p className="info-title">닉네임 규칙</p>
            <ul className="info-list">
              <li>3-30자 사이로 입력해주세요</li>
              <li>영문자, 숫자, 언더스코어(_)만 사용 가능합니다</li>
              <li>금칙어는 사용할 수 없습니다</li>
            </ul>
          </div>
        </section>

        {/* REQ-F-A2-Signup-4: Profile Section (to be implemented) */}
        <section className="profile-section">
          <h2 className="section-title">자기평가 정보</h2>
          <div className="placeholder-content">
            <p>🚧 자기평가 섹션은 REQ-F-A2-Signup-4에서 구현 예정입니다.</p>
          </div>
        </section>

        {/* REQ-F-A2-Signup-5/6: Submit Button (to be implemented) */}
        <div className="form-actions">
          <button
            type="button"
            className="submit-button"
            disabled={true}
          >
            가입 완료
          </button>
        </div>
      </div>
    </main>
  )
}

export default SignupPage
