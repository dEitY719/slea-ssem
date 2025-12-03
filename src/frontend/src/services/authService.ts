// Authentication service - centralizes all auth-related API calls
// REQ: REQ-F-A1-1, REQ-F-A1-2

import { transport } from '../lib/transport'

/**
 * Login request data
 */
export interface LoginRequest {
  knox_id: string
  name: string
  dept: string
  business_unit: string
  email: string
}

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
 * REQ-B-A0-API: Public API that returns auth state without throwing errors
 */
export interface AuthStatusResponse {
  authenticated: boolean
  nickname: string | null
  user_id: string | null
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
    return transport.get<AuthStatusResponse>('/auth/status', {
      accessLevel: 'public'
    })
  },

  /**
   * Login with Samsung AD credentials
   * REQ-B-A0-API: Public API (no auth required to login)
   *
   * @param userData - User data from Samsung AD
   * @returns Login response with JWT token
   */
  async login(userData: LoginRequest): Promise<LoginResponse> {
    return transport.post<LoginResponse>('/api/auth/login', userData, {
      accessLevel: 'public'
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
