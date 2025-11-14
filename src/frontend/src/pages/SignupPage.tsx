// REQ: REQ-F-A2-Signup-3, REQ-F-A2-Signup-4
import React, { useCallback, useMemo, useState } from 'react'
import { useNicknameCheck } from '../hooks/useNicknameCheck'
import './SignupPage.css'

/**
 * Unified Signup Page Component
 *
 * REQ: REQ-F-A2-Signup-3 - 통합 회원가입 페이지에 닉네임 입력 섹션 표시
 * REQ: REQ-F-A2-Signup-4 - 통합 회원가입 페이지에 자기평가 입력 섹션 표시 (수준만)
 *
 * Features:
 * - Nickname input section (REQ-F-A2-Signup-3)
 *   - Input field (3-30 characters)
 *   - Duplicate check button
 *   - Real-time validation
 *   - Suggestions on duplicate (up to 3)
 * - Profile input section (REQ-F-A2-Signup-4)
 *   - Level slider (1-5)
 * - Submit button (REQ-F-A2-Signup-5/6, to be implemented)
 *
 * Route: /signup
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

const SignupPage: React.FC = () => {
  // REQ-F-A2-Signup-3: Nickname state
  const {
    nickname,
    setNickname,
    checkStatus,
    errorMessage,
    suggestions,
    checkNickname,
  } = useNicknameCheck()

  // REQ-F-A2-Signup-4: Level state
  const [level, setLevel] = useState<number | null>(null)

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

  const handleLevelChange = useCallback((selectedLevel: number) => {
    setLevel(selectedLevel)
  }, [])

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

        {/* REQ-F-A2-Signup-4: Profile Section (Level only) */}
        <section className="profile-section">
          <h2 className="section-title">자기평가 정보</h2>

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
                    aria-label={option.label}
                  />
                  <div className="level-content">
                    <div className="level-label">{option.label}</div>
                    <div className="level-description">{option.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          <div className="info-box">
            <p className="info-title">향후 추가 예정</p>
            <ul className="info-list">
              <li>경력(연차) 입력</li>
              <li>직군 선택</li>
              <li>담당 업무 입력</li>
              <li>관심분야 다중 선택</li>
            </ul>
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
