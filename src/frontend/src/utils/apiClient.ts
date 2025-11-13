// API Client using Transport pattern
import { transport } from '../lib/transport'

/**
 * API Client with common HTTP methods
 *
 * This is a convenience wrapper around the transport layer.
 * Uses Transport pattern:
 * - Real backend in production
 * - Mock data in development (when VITE_MOCK_API=true or ?api_mock=true)
 *
 * Usage:
 * ```tsx
 * import { apiClient } from '../utils/apiClient'
 *
 * // GET request
 * const data = await apiClient.get<UserProfile>('/api/profile')
 *
 * // POST request
 * const result = await apiClient.post<LoginResponse>('/api/auth/login', {
 *   email: 'user@example.com'
 * })
 * ```
 */
export const apiClient = {
  /**
   * Send GET request
   */
  get: <T>(endpoint: string): Promise<T> => {
    return transport.get<T>(endpoint)
  },

  /**
   * Send POST request
   */
  post: <T>(endpoint: string, data?: any): Promise<T> => {
    return transport.post<T>(endpoint, data)
  },

  /**
   * Send PUT request
   */
  put: <T>(endpoint: string, data?: any): Promise<T> => {
    return transport.put<T>(endpoint, data)
  },

  /**
   * Send DELETE request
   */
  delete: <T>(endpoint: string): Promise<T> => {
    return transport.delete<T>(endpoint)
  },
}

/**
 * Re-export transport utilities for advanced usage
 */
export { transport, setMockScenario, setMockData, mockConfig } from '../lib/transport'
