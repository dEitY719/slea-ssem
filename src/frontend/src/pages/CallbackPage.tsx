// REQ: REQ-F-A1-2
import React from 'react'
import { useSearchParams } from 'react-router-dom'
import { PageLayout } from '../components'
import { useAuthCallback } from '../hooks/useAuthCallback'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { ErrorMessage } from '../components/ErrorMessage'
import './CallbackPage.css'

/**
 * SSO callback page for handling authentication
 *
 * Flow:
 * 1. Parse URL parameters (knox_id, name, dept, business_unit, email)
 * 2. Call backend authentication API
 * 3. Save JWT token to localStorage
 * 4. Redirect to home screen (/home)
 *
 * Supports mock mode for development/testing (add ?api_mock=true and/or ?sso_mock=true)
 */
const CallbackPage: React.FC = () => {
  const [searchParams] = useSearchParams()
  const { loading, error } = useAuthCallback(searchParams)

  if (loading && !error) {
    return (
      <PageLayout mainClassName="callback-page" containerClassName="callback-container">
        <LoadingSpinner message="로그인 처리 중입니다..." />
      </PageLayout>
    )
  }

  if (error) {
    return (
      <PageLayout mainClassName="callback-page" containerClassName="callback-container">
        <ErrorMessage
          title="로그인 실패"
          message={error}
          helpLinks={[
            {
              text: '계정 정보 확인',
              href: 'https://account.samsung.com',
            },
            {
              text: '관리자 문의',
              href: 'mailto:support@samsung.com',
            },
          ]}
        />
      </PageLayout>
    )
  }

  return null
}

export default CallbackPage
