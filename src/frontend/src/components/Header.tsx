// REQ: REQ-F-A2-Signup-1, REQ-F-A2-Profile-Access-1, REQ-F-A2-Profile-Access-2, REQ-F-A2-Profile-Access-3
import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  UserPlusIcon,
  UserCircleIcon,
  PencilSquareIcon,
  ChevronDownIcon,
} from '@heroicons/react/24/outline'
import './Header.css'
import './ProfileMenu.css'

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
    // Pass returnTo state so ProfileEditPage knows where to redirect after save
    navigate('/profile/edit', { state: { returnTo: '/home' } })
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
          <h1 className="header-logo">Learning Platform</h1>
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
                    <div className="nickname-content">
                      {/* <span className="nickname-label">프로필 관리</span> */}
                      <span className="nickname-text" title={nickname}>
                        {nickname}
                      </span>
                    </div>
                    <div className={`profile-dropdown-chevron${isDropdownOpen ? ' open' : ''}`} aria-hidden="true">
                      <ChevronDownIcon />
                    </div>
                    </button>
                    {/* REQ-F-A2-Profile-Access-3: Dropdown menu */}
                    {isDropdownOpen && (
                      <div className="profile-dropdown-menu" role="menu">
                        <div className="profile-dropdown-header" role="presentation">
                          <div className="dropdown-avatar">
                            <UserCircleIcon />
                          </div>
                          <div className="profile-dropdown-info">
                            <span className="profile-name-text">{nickname}</span>
                            <span className="profile-subtext">Learning Member</span>
                          </div>
                        </div>
                        <div className="profile-dropdown-divider" role="separator" />
                        <div className="profile-dropdown-body">
                          <button
                            type="button"
                            className="profile-dropdown-item"
                            onClick={handleEditProfileClick}
                            role="menuitem"
                          >
                            <span className="profile-menu-icon-pill">
                              <PencilSquareIcon className="profile-menu-icon" />
                            </span>
                            <span className="profile-dropdown-item-text">
                              <span className="profile-dropdown-item-title">프로필 수정</span>
                              <span className="profile-dropdown-item-desc">학습 정보와 관심 분야를 업데이트</span>
                            </span>
                          </button>
                        </div>
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
