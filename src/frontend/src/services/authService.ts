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
 * Authentication service
 * Handles all authentication-related API calls
 */
export const authService = {
  /**
   * Login with Samsung AD credentials
   *
   * @param userData - User data from Samsung AD
   * @returns Login response with JWT token
   */
  async login(userData: LoginRequest): Promise<LoginResponse> {
    return transport.post<LoginResponse>('/api/auth/login', userData)
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
