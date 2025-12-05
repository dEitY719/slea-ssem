// Transport factory - selects between real and mock transport

import { HttpTransport, RequestConfig } from './types'
import { realTransport } from './realTransport'
import { mockTransport } from './mockTransport'

/**
 * Check if mock mode is enabled
 * Priority: URL param (temporary override) > Environment variable
 */
function isMockMode(): boolean {
  // Check URL parameter for temporary override
  // Usage: ?api_mock=true or legacy ?mock=true
  const urlParams = new URLSearchParams(window.location.search)
  const mockFlag = urlParams.get('api_mock') ?? urlParams.get('mock')
  if (mockFlag === 'true') return true
  if (mockFlag === 'false') return false

  // Check environment variable (primary configuration in .env)
  return import.meta.env.VITE_MOCK_API === 'true'
}

/**
 * Get the appropriate transport based on mode
 */
export function getTransport(): HttpTransport {
  return isMockMode() ? mockTransport : realTransport
}

/**
 * Lazy transport proxy that always delegates to the active transport.
 * This allows tests to toggle mock mode (e.g., via URL params) even
 * after modules have been imported.
 */
export const transport: HttpTransport = {
  get<T>(url: string, config?: RequestConfig) {
    return getTransport().get<T>(url, config)
  },
  post<T>(url: string, data?: any, config?: RequestConfig) {
    return getTransport().post<T>(url, data, config)
  },
  put<T>(url: string, data?: any, config?: RequestConfig) {
    return getTransport().put<T>(url, data, config)
  },
  delete<T>(url: string, config?: RequestConfig) {
    return getTransport().delete<T>(url, config)
  },
}

// Re-export types and utilities
export type { HttpTransport, RequestConfig } from './types'
export {
  setMockScenario,
  setMockData,
  setMockAuthState,
  mockConfig,
  getMockData,
  getMockRequests,
  clearMockRequests,
  setMockError,
  clearMockErrors,
  resetMockResults,
} from './mockTransport'
