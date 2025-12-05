// ContinuePage - Intent-based router for continue flows
// Purpose: Thin router that delegates to intent handlers

import React, { useEffect, useRef, useState } from 'react'
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { PageLayout } from '../components'
import { handleServiceLogin } from '../features/continue/handleServiceLogin'
import { handleLeveltest } from '../features/continue/handleLeveltest'
import type { ContinueIntent, ContinueContext } from '../features/continue/types'
import './SSOPage.css'

/**
 * ContinuePage - Intent-based router
 *
 * Routes based on ?intent query parameter:
 * - intent=service_login → handleServiceLogin
 * - intent=leveltest → handleLeveltest
 * - default → redirect to /
 *
 * This page acts as a continuation point after SSO/signup flows.
 */
const GENERIC_ERROR_MESSAGE = '알 수 없는 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'

const ContinuePage: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const [error, setError] = useState<string | null>(null)
  const lastProcessedSearch = useRef<string | null>(null)

  useEffect(() => {
    const currentSearch = location.search

    // Avoid duplicate processing when StrictMode re-runs effects or search params repeat
    if (lastProcessedSearch.current === currentSearch) {
      return
    }
    lastProcessedSearch.current = currentSearch

    const processIntent = async () => {
      const intent = searchParams.get('intent') as ContinueIntent | null
      const returnTo = searchParams.get('returnTo') || undefined

      const ctx: ContinueContext = {
        navigate,
        returnTo,
      }

      try {
        switch (intent) {
          case 'service_login':
            await handleServiceLogin(ctx)
            break

          case 'leveltest':
            await handleLeveltest(ctx)
            break

          default:
            console.warn('[Continue] Unknown or missing intent, redirecting to /')
            navigate('/', { replace: true })
            break
        }
      } catch (err) {
        console.error('[Continue] Intent handler failed:', err)
        setError(GENERIC_ERROR_MESSAGE)
      }
    }

    processIntent()
  }, [location.search, navigate, searchParams])

  if (error) {
    return (
      <PageLayout mainClassName="continue-page" containerClassName="continue-container">
        <div data-testid="continue-container">
          <h1 className="continue-title">SLEA-SSEM</h1>
          <p>{error}</p>
          <button onClick={() => navigate('/')}>홈으로 돌아가기</button>
        </div>
      </PageLayout>
    )
  }

  return (
    <PageLayout mainClassName="continue-page" containerClassName="continue-container">
      <div data-testid="continue-container">
        <h1 className="continue-title">SLEA-SSEM</h1>
        <p>처리 중...</p>
      </div>
    </PageLayout>
  )
}

export default ContinuePage
