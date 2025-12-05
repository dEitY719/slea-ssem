// REQ: REQ-F-A2-Signup-3, REQ-F-A2-Signup-4, REQ-F-A2-Signup-5, REQ-F-A2-Signup-6
import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageLayout } from '../components'
import { useNicknameCheck } from '../hooks/useNicknameCheck'
import { completeProfileSignup } from '../features/profile/profileSubmission'
import { authService } from '../services/authService'
import NicknameInputSection from '../components/NicknameInputSection'
import CareerInfoSection from '../components/CareerInfoSection'
import LevelSelector from '../components/LevelSelector'
import RadioButtonGrid, { type RadioButtonOption } from '../components/RadioButtonGrid'
import './SignupPage.css'

/**
 * Unified Signup Page Component
 *
 * REQ: REQ-F-A2-Signup-3 - 통합 회원가입 페이지에 닉네임 입력 섹션 표시
 * REQ: REQ-F-A2-Signup-4 - 통합 회원가입 페이지에 자기평가 입력 섹션 표시
 *   - 수준 (1~5 슬라이더)
 *   - 경력(연차): 숫자 입력 (0-50)
 *   - 직군: 라디오버튼 (S, E, M, G, F)
 *   - 담당 업무: 텍스트 입력
 *   - 관심분야: 라디오버튼 (AI, ML, Backend, Frontend)
 * REQ: REQ-F-A2-Signup-5 - 닉네임 중복 확인 완료 + 모든 필수 필드 입력 시 "가입 완료" 버튼 활성화
 * REQ: REQ-F-A2-Signup-6 - "가입 완료" 버튼 클릭 시 nickname + profile 저장 후 홈화면으로 리다이렉트
 *
 * Features:
 * - Nickname input section (REQ-F-A2-Signup-3)
 *   - Input field (3-30 characters)
 *   - Duplicate check button
 *   - Real-time validation
 *   - Suggestions on duplicate (up to 3)
 * - Profile input sections (REQ-F-A2-Signup-4)
 *   - Career info: career, jobRole, duty (CareerInfoSection)
 *   - Interests: RadioButtonGrid
 *   - Level: LevelSelector (1-5)
 * - Submit button activation (REQ-F-A2-Signup-5)
 *   - Enabled when: checkStatus === 'available' AND level !== null
 *   - Disabled otherwise
 * - Signup submission (REQ-F-A2-Signup-6)
 *   - Calls registerNickname API
 *   - Calls updateSurvey API with all fields
 *   - Redirects to home on success
 *
 * Route: /signup
 */

// Radio button options for Interests field
const INTERESTS_OPTIONS: RadioButtonOption[] = [
  { value: 'AI', label: 'AI' },
  { value: 'ML', label: 'ML' },
  { value: 'Backend', label: 'Backend' },
  { value: 'Frontend', label: 'Frontend' },
]

const SignupPage: React.FC = () => {
  // REQ-F-A2-Signup-3: Nickname state (from useNicknameCheck hook)
  const {
    nickname,
    setNickname,
    checkStatus,
    errorMessage,
    suggestions,
    checkNickname,
  } = useNicknameCheck()

  // REQ-F-A2-Signup-4: Profile state
  const [career, setCareer] = useState<number>(0)
  const [jobRole, setJobRole] = useState<string>('')
  const [duty, setDuty] = useState<string>('')
  const [interests, setInterests] = useState<string>('')
  const [level, setLevel] = useState<number | null>(null)

  // REQ-F-A2-Signup-6: Submit state
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [isCheckingAuth, setIsCheckingAuth] = useState(true)
  const navigate = useNavigate()

  // Check SSO authentication before allowing signup
  useEffect(() => {
    const checkAuth = async () => {
      try {
        // Call checkSignupEligibility (Private-Auth API)
        // - If no SSO (401 + NEED_SSO) → transport redirects to /sso?returnTo=/signup
        // - If SSO valid → returns auth status, proceed with signup
        await authService.checkSignupEligibility()

        console.log('[Signup] SSO authentication verified')
        setIsCheckingAuth(false)
      } catch (err) {
        console.error('[Signup] SSO check failed:', err)
        // If error is thrown (not redirect), show error
        setSubmitError(err instanceof Error ? err.message : 'SSO 인증 확인 실패')
        setIsCheckingAuth(false)
      }
    }

    checkAuth()
  }, [])

    // REQ-F-A2-Signup-5: Submit button activation logic
    // Enable when: auth check complete AND nickname is available AND level is selected AND not submitting
    const isSubmitDisabled = useMemo(() => {
      return isCheckingAuth || checkStatus !== 'available' || level === null || isSubmitting
    }, [isCheckingAuth, checkStatus, level, isSubmitting])

    // REQ-F-A2-Signup-6: Submit handler
    const handleSubmit = useCallback(async () => {
      if (isSubmitDisabled || isSubmitting) return

      setIsSubmitting(true)
      setSubmitError(null)

      try {
        await completeProfileSignup({
          nickname,
          level: level!,
          career,
          jobRole,
          duty,
          interests,
        })

        navigate('/home', { replace: true })
      } catch (error) {
        const message =
          error instanceof Error ? error.message : '가입 완료에 실패했습니다.'
        setSubmitError(message)
        setIsSubmitting(false)
      }
    }, [nickname, level, career, jobRole, duty, interests, isSubmitting, isSubmitDisabled, navigate])

  return (
    <PageLayout mainClassName="signup-page" containerClassName="signup-container">
      <h1 className="page-title">회원가입</h1>
        <p className="page-description">
          닉네임과 자기평가 정보를 입력하여 가입을 완료하세요.
        </p>

        {/* SSO authentication check loading */}
        {isCheckingAuth && (
          <div className="auth-check-loading">
            <p>SSO 인증 확인 중...</p>
          </div>
        )}

        {/* REQ-F-A2-Signup-3: Nickname Section */}
        <NicknameInputSection
          nickname={nickname}
          setNickname={setNickname}
          checkStatus={checkStatus}
          errorMessage={errorMessage}
          suggestions={suggestions}
          onCheckClick={checkNickname}
          disabled={isCheckingAuth || isSubmitting}
          showInfoBox={true}
        />

        {/* REQ-F-A2-Signup-4: Career Info Section */}
        <div className="form-section">
          <h2 className="section-title">경력 정보</h2>
          <CareerInfoSection
            career={career}
            jobRole={jobRole}
            duty={duty}
            onCareerChange={setCareer}
            onJobRoleChange={setJobRole}
            onDutyChange={setDuty}
            disabled={isCheckingAuth || isSubmitting}
            showTitle={false}
          />
        </div>

        {/* REQ-F-A2-Signup-4: Interests & Level Section */}
        <div className="form-section">
          <h2 className="section-title">관심분야 및 기술 수준</h2>

          {/* Interests */}
          <RadioButtonGrid
            name="interests"
            legend="관심분야"
            options={INTERESTS_OPTIONS}
            value={interests}
            onChange={setInterests}
            disabled={isCheckingAuth || isSubmitting}
          />

          {/* Level */}
          <LevelSelector
            value={level}
            onChange={setLevel}
            disabled={isCheckingAuth || isSubmitting}
            showTitle={true}
          />
        </div>

        {/* REQ-F-A2-Signup-5/6: Submit Button */}
        <div className="form-actions">
          {submitError && (
            <p className="submit-error-message">{submitError}</p>
          )}
          <button
            type="button"
            className="submit-button"
            disabled={isSubmitDisabled}
            onClick={handleSubmit}
          >
            {isCheckingAuth ? 'SSO 인증 확인 중...' : isSubmitting ? '가입 중...' : '가입 완료'}
          </button>
        </div>
    </PageLayout>
  )
}

export default SignupPage
