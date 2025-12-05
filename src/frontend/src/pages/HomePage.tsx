// REQ: REQ-F-A1-2, REQ-F-A2-1, REQ-F-A3, REQ-F-A2-Signup-1, REQ-F-A1-Home, REQ-F-A1-Error-1
import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { PlayIcon } from '@heroicons/react/24/outline'
import { TrophyIcon } from '@heroicons/react/24/solid'
import { useUserProfile } from '../hooks/useUserProfile'
import { homeService, type LastTestResult } from '../services/homeService'
import { PageLayout } from '../components'
import { getLevelClass, getLevelKorean, getLevelGradeString } from '../utils/gradeHelpers'
import './HomePage.css'

const HomePage: React.FC = () => {
  const navigate = useNavigate()
  const { nickname, loading: nicknameLoading, checkNickname } = useUserProfile()

  // REQ: REQ-F-A1-Home - Last test result state
  const [lastTestResult, setLastTestResult] = useState<LastTestResult | null>(null)
  const [isLoadingResult, setIsLoadingResult] = useState(true)

  // REQ: REQ-F-A1-Home - Total participants state
  const [totalParticipants, setTotalParticipants] = useState<number | null>(null)
  const [isLoadingStats, setIsLoadingStats] = useState(true)

  // REQ-F-A0-Landing-2: No authentication check, render for all users
  // HomePage is now accessible to unauthenticated users as landing page

  // REQ-F-A2-Signup-1: Load nickname to determine if user data should be fetched
  // Note: Nickname is loaded by App.tsx and passed to Header
  // HomePage uses useUserProfile hook which calls authService.getAuthStatus() (Public API)
  useEffect(() => {
    const loadNickname = async () => {
      try {
        // Use Public API to get auth status (includes nickname)
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

    const handleStart = () => {
      // Navigate to /continue with intent=leveltest
      // ContinuePage will delegate to handleLeveltest:
      // - Check consent status
      // - Check nickname status
      // - Navigate to appropriate page based on status
      navigate('/continue?intent=leveltest')
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
