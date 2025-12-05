// Authentication service - centralizes all auth-related API calls
// REQ: REQ-F-A1-1, REQ-F-A1-2

import { transport } from '../lib/transport'

/**
 * Login response from backend
 */
export interface LoginResponse {
  access_token: string
  token_type: string
  user_id: string
  is_new_user: boolean
}

/**
 * Auth status response
 * REQ-B-A1-9: Public API that returns SSO auth state
 */
export interface AuthStatusResponse {
  authenticated: boolean
  user_id: number | null
  knox_id: string | null
}

/**
 * Authentication service
 * Handles all authentication-related API calls
 */
export const authService = {
  /**
   * Check authentication status
   * REQ-B-A0-API: Public API that checks auth state without throwing errors
   *
   * @returns Auth status including authentication state and nickname
   */
  async getAuthStatus(): Promise<AuthStatusResponse> {
    return transport.get<AuthStatusResponse>('/api/auth/status', {
      accessLevel: 'public'
    })
  },

  /**
   * Login with Samsung AD credentials
   * REQ-B-A0-API: Private-Auth API (checks SSO, then membership)
   *
   * @returns Login response with JWT token
   */
  async login(): Promise<LoginResponse> {
    return transport.post<LoginResponse>('/api/auth/login', undefined, {
      accessLevel: 'private-auth'
    })
  },

  /**
   * Check signup eligibility (SSO authentication required)
   * REQ-B-A0-API: Private-Auth API (checks SSO only)
   *
   * This triggers SSO authentication flow if not authenticated.
   * Backend returns auth status if SSO is valid.
   *
   * @returns Auth status after SSO check
   */
  async checkSignupEligibility(): Promise<AuthStatusResponse> {
    return transport.get<AuthStatusResponse>('/api/auth/signup-check', {
      accessLevel: 'private-auth'
    })
  },

  /**
   * Logout (HttpOnly cookie-based)
   * TODO: Call backend /auth/logout to clear cookie
   */
  logout(): void {
    // HttpOnly cookie cannot be removed from client-side
    // Backend should provide /auth/logout endpoint to clear cookie
  },
}
