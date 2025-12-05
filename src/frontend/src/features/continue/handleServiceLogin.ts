// Handle service_login intent
// Purpose: Login flow - check SSO + membership, then navigate to home

import { authService } from '../../services/authService'
import type { ContinueContext } from './types'

/**
 * Handle service_login intent
 *
 * Flow:
 * 1. Call POST /api/auth/login (Private-Auth API)
 * 2. Backend checks: SSO authentication → membership status
 * 3. If 401 NEED_SSO → transport redirects to /sso?returnTo=/continue?intent=service_login
 * 4. If 403 NEED_SIGNUP → transport redirects to /signup?returnTo=/continue?intent=service_login
 * 5. If success → navigate to /home
 *
 * @param ctx - Continue context with navigate function + optional returnTo target
 * @throws Error on unexpected failures (401/403 handled by transport)
 */
export async function handleServiceLogin(ctx: ContinueContext): Promise<void> {
  console.log('[Continue] Handling service_login intent')

  try {
    // Call login API (Private-Auth)
    // - If no SSO (401 + NEED_SSO) → transport redirects to /sso
    // - If not member (403 + NEED_SIGNUP) → transport redirects to /signup
    // - If success → authenticated and member
    await authService.login()

    // Success: user is authenticated and member
    console.log('[Continue] Service login successful, navigating to /home')
    ctx.navigate(ctx.returnTo ?? '/home', { replace: true })
  } catch (err) {
    // Only unexpected errors reach here (401/403 handled by transport)
    console.error('[Continue] Service login failed:', err)
    throw err
  }
}
