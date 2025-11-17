// REQ: REQ-F-A2-Signup-1, REQ-F-A2-Profile-Access-1
import React from 'react'
import { useNavigate } from 'react-router-dom'
import { UserPlusIcon, UserCircleIcon } from '@heroicons/react/24/outline'
import './Header.css'

interface HeaderProps {
  /**
   * User's nickname. If null, user hasn't completed signup yet.
   * REQ-F-A2-Signup-1: Show "회원가입" button only when nickname is null
   * REQ-F-A2-Profile-Access-1: Show nickname when not null
   */
  nickname: string | null

  /**
   * Loading state for nickname fetch
   * Hide signup button while loading to prevent flickering
   */
  isLoading?: boolean
}

/**
 * Header Component
 *
 * REQ-F-A2-Signup-1: Display "회원가입" button in header when nickname is null
 * REQ-F-A2-Profile-Access-1: Display user's nickname in header when nickname is not null
 *
 * Displays site header with conditional content in header-right:
 * - nickname === null: Show "회원가입" button (user hasn't signed up)
 * - nickname !== null: Show user's nickname (user already signed up)
 * - isLoading === true: Show nothing (prevent flickering)
 *
 * @param nickname - User's nickname (null if not set)
 * @param isLoading - Loading state for nickname fetch
 */
export const Header: React.FC<HeaderProps> = ({ nickname, isLoading = false }) => {
  const navigate = useNavigate()

  const handleSignupClick = () => {
    // REQ-F-A2-Signup-2: Navigate to /signup page
    navigate('/signup')
  }

  const shouldRenderControls = !isLoading

  return (
    <header className="app-header">
      <div className="header-container">
        <div className="header-left">
          <h1 className="header-logo">S.LSI Learning Platform</h1>
        </div>

        <div className="header-right">
          {shouldRenderControls && (
            <>
              {/* REQ-F-A2-Signup-1: Show "회원가입" button only when nickname is null */}
              {nickname === null && (
                <button
                  className="signup-button"
                  onClick={handleSignupClick}
                  aria-label="회원가입 페이지로 이동"
                >
                  <UserPlusIcon className="button-icon" />
                  회원가입
                </button>
              )}

              {/* REQ-F-A2-Profile-Access-1: Show nickname when not null */}
              {nickname !== null && (
                <div className="nickname-display" aria-label={`현재 로그인: ${nickname}`}>
                  <div className="profile-icon">
                    <UserCircleIcon />
                  </div>
                  <span className="nickname-text">{nickname}</span>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </header>
  )
}
