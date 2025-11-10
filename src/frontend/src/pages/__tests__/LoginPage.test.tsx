// REQ: REQ-F-A1-1
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import LoginPage from '../LoginPage'

describe('LoginPage', () => {
  // Test 1: Happy Path - 로그인 페이지 렌더링
  it('should render login page successfully', () => {
    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )
    expect(screen.getByRole('main')).toBeInTheDocument()
  })

  // Test 2: Happy Path - "Samsung AD로 로그인" 버튼 표시
  it('should display "Samsung AD로 로그인" button clearly', () => {
    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )
    const loginButton = screen.getByRole('button', { name: /Samsung AD로 로그인/i })
    expect(loginButton).toBeInTheDocument()
    expect(loginButton).toBeVisible()
  })

  // Test 3: Happy Path - 버튼 클릭 시 리다이렉트 (개발 모드)
  it('should redirect to /auth/callback?mock=true in development mode', () => {
    const originalLocation = window.location
    // @ts-ignore
    delete window.location
    window.location = { href: '' } as Location

    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )
    const loginButton = screen.getByRole('button', { name: /Samsung AD로 로그인/i })

    fireEvent.click(loginButton)

    // 개발 모드에서는 mock 모드로 콜백 페이지로 리다이렉트
    expect(window.location.href).toBe('/auth/callback?mock=true')

    // Cleanup
    window.location = originalLocation
  })

  // Test 4: Acceptance Criteria - 버튼 접근성 검증
  it('should have accessible button with proper aria attributes', () => {
    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )
    const loginButton = screen.getByRole('button', { name: /Samsung AD로 로그인/i })

    expect(loginButton).toHaveAttribute('type', 'button')
    expect(loginButton).not.toBeDisabled()
  })

  // Test 5: Edge Case - 컨테이너가 중앙 정렬 클래스를 가짐
  it('should have container with proper styling classes', () => {
    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )
    const container = screen.getByTestId('login-container')

    expect(container).toHaveClass('login-container')
    expect(container).toBeInTheDocument()
  })
})
