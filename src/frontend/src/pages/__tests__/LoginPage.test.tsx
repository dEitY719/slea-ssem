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
  it('should redirect to SSO mock callback with default parameters when API mock is disabled', () => {
    const originalLocation = window.location
    const originalMockApi = import.meta.env.VITE_MOCK_API
    const originalMockSso = import.meta.env.VITE_MOCK_SSO
    // @ts-ignore
    delete window.location
    window.location = { href: '' } as Location
    import.meta.env.VITE_MOCK_API = 'false'
    import.meta.env.VITE_MOCK_SSO = 'true'

    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )
    const loginButton = screen.getByRole('button', { name: /Samsung AD로 로그인/i })

    fireEvent.click(loginButton)

    const redirectedUrl = new URL(window.location.href, 'http://localhost')
    expect(redirectedUrl.pathname).toBe('/auth/callback')
    expect(redirectedUrl.searchParams.get('sso_mock')).toBe('true')
    expect(redirectedUrl.searchParams.get('knox_id')).toBe('mock_user_001')
    expect(redirectedUrl.searchParams.get('name')).toBe('Mock User')
    expect(redirectedUrl.searchParams.get('dept')).toBe('Mock Department')
    expect(redirectedUrl.searchParams.get('business_unit')).toBe('S.LSI')
    expect(redirectedUrl.searchParams.get('email')).toBe('mock.user@samsung.com')
    expect(redirectedUrl.searchParams.has('api_mock')).toBe(false)
    expect(redirectedUrl.searchParams.has('mock')).toBe(false)

    if (originalMockApi === undefined) {
      delete import.meta.env.VITE_MOCK_API
    } else {
      import.meta.env.VITE_MOCK_API = originalMockApi
    }
    if (originalMockSso === undefined) {
      delete import.meta.env.VITE_MOCK_SSO
    } else {
      import.meta.env.VITE_MOCK_SSO = originalMockSso
    }
    window.location = originalLocation
  })

  it('should include api_mock flag when backend mock mode is enabled', () => {
    const originalLocation = window.location
    const originalMockApi = import.meta.env.VITE_MOCK_API
    const originalMockSso = import.meta.env.VITE_MOCK_SSO
    // @ts-ignore
    delete window.location
    window.location = { href: '' } as Location
    import.meta.env.VITE_MOCK_API = 'true'
    import.meta.env.VITE_MOCK_SSO = 'true'

    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )
    const loginButton = screen.getByRole('button', { name: /Samsung AD로 로그인/i })

    fireEvent.click(loginButton)

    const redirectedUrl = new URL(window.location.href, 'http://localhost')
    expect(redirectedUrl.pathname).toBe('/auth/callback')
    expect(redirectedUrl.searchParams.get('api_mock')).toBe('true')
    expect(redirectedUrl.searchParams.get('mock')).toBe('true')

    if (originalMockApi === undefined) {
      delete import.meta.env.VITE_MOCK_API
    } else {
      import.meta.env.VITE_MOCK_API = originalMockApi
    }
    if (originalMockSso === undefined) {
      delete import.meta.env.VITE_MOCK_SSO
    } else {
      import.meta.env.VITE_MOCK_SSO = originalMockSso
    }
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
