// REQ: REQ-F-A1-1, REQ-F-A1-3, REQ-B-A1-9
import { transport } from '../lib/transport'

/**
 * Authentication utility functions for HttpOnly cookie-based auth.
 *
 * MIGRATION NOTE (2025-01):
 * - Removed: saveToken, getToken, removeToken (localStorage 방식)
 * - Migrated to HttpOnly cookie (XSS 방어)
 * - JWT는 서버에서 Set-Cookie로 관리
 * - 브라우저가 자동으로 모든 요청에 쿠키 포함
 */

/**
 * Check if user is authenticated via GET /api/auth/status
 * (HttpOnly cookie is automatically included by browser)
 *
 * REQ: REQ-F-A1-3, REQ-B-A1-9
 *
 * @returns Promise<boolean> - true if authenticated field is true, false otherwise
 */
export const isAuthenticated = async (): Promise<boolean> => {
  try {
    // Use transport layer to respect VITE_MOCK_API setting
    const response = await transport.get<{ authenticated: boolean }>('/api/auth/status')
    // Check authenticated field explicitly (handles soft logout, expired sessions with 200 OK)
    return response.authenticated === true
  } catch {
    return false // 401 or any error = not authenticated
  }
}
