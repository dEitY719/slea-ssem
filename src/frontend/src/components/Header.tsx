// REQ: REQ-F-A2-Signup-1, REQ-F-A2-Profile-Access-1, REQ-F-A2-Profile-Access-2, REQ-F-A2-Profile-Access-3
import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { UserPlusIcon, UserCircleIcon, PencilSquareIcon } from '@heroicons/react/24/outline'
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
 * REQ-F-A2-Profile-Access-2: Make nickname clickable with visual feedback (hover/active)
 * REQ-F-A2-Profile-Access-3: Show dropdown menu when nickname is clicked
 * REQ-F-A2-Profile-Access-4: Dropdown contains "프로필 수정" menu item
 * REQ-F-A2-Profile-Access-5: Navigate to /profile/edit when "프로필 수정" is clicked
 * REQ-F-A2-Profile-Access-6: Close dropdown when clicking outside
 *
 * Displays site header with conditional content in header-right:
 * - nickname === null: Show "회원가입" button (user hasn't signed up)
 * - nickname !== null: Show user's nickname as clickable button (user already signed up)
 * - isLoading === true: Show nothing (prevent flickering)
 *
 * @param nickname - User's nickname (null if not set)
 * @param isLoading - Loading state for nickname fetch
 */
export const Header: React.FC<HeaderProps> = ({ nickname, isLoading = false }) => {
  const navigate = useNavigate()
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const handleSignupClick = () => {
    // REQ-F-A2-Signup-2: Navigate to /signup page
    navigate('/signup')
  }

  const handleNicknameClick = () => {
    // REQ-F-A2-Profile-Access-3: Toggle dropdown menu
    setIsDropdownOpen(prev => !prev)
  }

  const handleEditProfileClick = () => {
    // REQ-F-A2-Profile-Access-5: Navigate to profile edit page
    navigate('/profile/edit')
    setIsDropdownOpen(false)
  }

  // REQ-F-A2-Profile-Access-6: Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false)
      }
    }

    if (isDropdownOpen) {
      document.addEventListener('click', handleClickOutside)
    }

    return () => {
      document.removeEventListener('click', handleClickOutside)
    }
  }, [isDropdownOpen])

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

              {/* REQ-F-A2-Profile-Access-3: Show nickname as clickable button with dropdown */}
              {nickname !== null && (
                <div className="profile-menu-container" ref={dropdownRef}>
                  <button
                    type="button"
                    className="nickname-display"
                    onClick={handleNicknameClick}
                    aria-label={`프로필 메뉴 열기 - 현재 로그인: ${nickname}`}
                    aria-expanded={isDropdownOpen}
                  >
                    <div className="profile-icon">
                      <UserCircleIcon />
                    </div>
                    <span className="nickname-text">{nickname}</span>
                  </button>

                  {/* REQ-F-A2-Profile-Access-3: Dropdown menu */}
                  {isDropdownOpen && (
                    <div className="dropdown-menu" role="menu">
                      <button
                        type="button"
                        className="dropdown-item"
                        onClick={handleEditProfileClick}
                        role="menuitem"
                      >
                        <PencilSquareIcon className="menu-icon" />
                        프로필 수정
                      </button>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </header>
  )
}
