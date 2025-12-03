// REQ: REQ-F-A1-2, REQ-F-A2-1, REQ-F-A3, REQ-F-A2-Signup-1, REQ-F-A1-Home, REQ-F-A1-Error-1
import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { PlayIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import { TrophyIcon } from '@heroicons/react/24/solid'
import { isAuthenticated } from '../utils/auth'
import { detectRedirectLoop, resetRedirectDetection } from '../utils/redirectDetection'
import { useUserProfile } from '../hooks/useUserProfile'
import { profileService } from '../services/profileService'
import { homeService, type LastTestResult } from '../services/homeService'
import { PageLayout } from '../components'
import { getLevelClass, getLevelKorean, getLevelGradeString } from '../utils/gradeHelpers'
import './HomePage.css'

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

const HomePage: React.FC = () => {
  const navigate = useNavigate()
  const { nickname, loading: nicknameLoading, checkNickname } = useUserProfile()
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // REQ: REQ-F-A1-Home - Last test result state
  const [lastTestResult, setLastTestResult] = useState<LastTestResult | null>(null)
  const [isLoadingResult, setIsLoadingResult] = useState(true)

  // REQ: REQ-F-A1-Home - Total participants state
  const [totalParticipants, setTotalParticipants] = useState<number | null>(null)
  const [isLoadingStats, setIsLoadingStats] = useState(true)

  // REQ-F-A0-Landing-2: No authentication check, render for all users
  // HomePage is now accessible to unauthenticated users as landing page

  // REQ-F-A2-Signup-1: Load nickname to determine if user data should be fetched
  useEffect(() => {
    const loadNickname = async () => {
      try {
        await checkNickname()
      } catch (err) {
        console.error('Failed to load nickname:', err)
        // Silently fail for nickname check, user can still use the page
      }
    }

    loadNickname()
  }, [checkNickname])

  // REQ: REQ-F-A1-Home-1, REQ-F-A1-Home-2 - Fetch last test result (only if logged in)
  useEffect(() => {
    // Skip loading if nickname is not set (user not logged in)
    if (nicknameLoading) {
      return
    }

    if (!nickname) {
      setIsLoadingResult(false)
      setLastTestResult({ hasResult: false, grade: null, completedAt: null, badgeUrl: null })
      return
    }

    const fetchLastTestResult = async () => {
      setIsLoadingResult(true)
      try {
        const result = await homeService.getLastTestResult()
        setLastTestResult(result)
      } catch (err) {
        console.error('Failed to fetch last test result:', err)
        // Set default no-result state
        setLastTestResult({ hasResult: false, grade: null, completedAt: null, badgeUrl: null })
      } finally {
        setIsLoadingResult(false)
      }
    }

    fetchLastTestResult()
  }, [nickname, nicknameLoading])

  // REQ: REQ-F-A1-Home-4 - Fetch total participants (only if logged in)
  useEffect(() => {
    // Skip loading if nickname is not set (user not logged in)
    if (nicknameLoading) {
      return
    }

    if (!nickname) {
      setIsLoadingStats(false)
      setTotalParticipants(null)
      return
    }

    const fetchTotalParticipants = async () => {
      setIsLoadingStats(true)
      try {
        const stats = await homeService.getTotalParticipants()
        setTotalParticipants(stats.totalParticipants)
      } catch (err) {
        console.error('Failed to fetch total participants:', err)
        setTotalParticipants(null)
      } finally {
        setIsLoadingStats(false)
      }
    }

    fetchTotalParticipants()
  }, [nickname, nicknameLoading])

    const handleStart = async () => {
      try {
        // REQ-F-A3-5: Check consent status first
        const consentStatus = await profileService.getConsentStatus()

        if (!consentStatus.consented) {
          // User hasn't consented yet, redirect to consent page
          navigate('/consent')
          return
        }

        // REQ-F-A2-1: Check if user has set nickname before proceeding
        const currentNickname = await checkNickname()
        const { surveyId, level } = getSurveyProgress()

        if (currentNickname === null) {
          // User hasn't set nickname yet, redirect to nickname setup
          navigate('/nickname-setup')
        } else if (surveyId) {
          // User completed profile, show review page for final confirmation/test entry
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
        // Log detailed error for debugging
        console.error('Failed to check user profile:', err)

        // Show user-friendly error message with hint
        const errorMsg = err instanceof Error ? err.message : 'Unknown error'
        setErrorMessage(`프로필 정보를 불러오는데 실패했습니다: ${errorMsg}`)
      }
    }

  return (
    <PageLayout
      showHeader
      nickname={nickname}
      isNicknameLoading={nicknameLoading}
      mainClassName="home-page"
      containerClassName="home-container"
    >
      <div className="home-sections">
        {/* Section 1: 메인 CTA */}
        <section className="home-section">
          <div className="home-content">
            <p className="home-label">TODAY'S LEVEL</p>
            <h1 className="home-title">
              오늘 당신의 AI 역량은?<br/>
            </h1>
            <p className="home-description">
              슬아샘과 함께 개인 맞춤형 테스트로 당신의 실력을 객관적으로 측정해보세요.
            </p>

            {errorMessage && (
              <div className="error-message">
                <ExclamationTriangleIcon className="error-icon" />
                <span>{errorMessage}</span>
              </div>
            )}

            <div className="level-button-group">
              <button className="level-start-button" onClick={handleStart}>
                <PlayIcon className="button-icon" />
                레벨테스트 시작하기
              </button>
            </div>
          </div>

          {/* REQ: REQ-F-A1-Home-1, REQ-F-A1-Home-2, REQ-F-A1-Home-3, REQ-F-A1-Home-4 */}
          <div className="info-card">
            <div style={{ marginBottom: '1.5rem' }}>
              <div className="level-card-header">
                <p className="info-card-title">나의 현재 레벨</p>
                {lastTestResult?.hasResult && lastTestResult.completedAt && (
                  <span className="date-badge">{lastTestResult.completedAt} 기준</span>
                )}
              </div>
              {isLoadingResult ? (
                <p className="info-card-value">...</p>
              ) : lastTestResult?.hasResult ? (
                <div className={`home-grade-badge ${getLevelClass(lastTestResult.grade)}`}>
                  <TrophyIcon className="home-grade-icon" />
                  <div className="home-grade-info">
                    <p className="home-grade-value">{getLevelKorean(lastTestResult.grade)}</p>
                    <p className="home-grade-english">{getLevelGradeString(lastTestResult.grade)}</p>
                  </div>
                </div>
              ) : (
                <>
                  <p className="info-card-value">-</p>
                  <p className="home-description" style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>
                    테스트를 완료하면<br/>당신의 레벨이 표시됩니다
                  </p>
                </>
              )}
            </div>

            <div style={{ borderTop: '1px solid var(--border-card)', paddingTop: '1rem' }}>
              {isLoadingStats ? (
                <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                  로딩 중...
                </p>
              ) : totalParticipants !== null ? (
                <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                  전체 <strong style={{ color: 'var(--text-primary)' }}>{totalParticipants.toLocaleString()}</strong>명 참여
                </p>
              ) : (
                <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                  참여자 정보 없음
                </p>
              )}
            </div>
          </div>
        </section>
      </div>
    </PageLayout>
  )
}

export default HomePage
