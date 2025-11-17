// Transport factory - selects between real and mock transport

import { HttpTransport } from './types'
import { realTransport } from './realTransport'
import { mockTransport } from './mockTransport'

/**
 * Check if mock mode is enabled
 * Priority: URL param > localStorage > Environment variable
 */
function isMockMode(): boolean {
  // Check URL parameter first (for testing: ?api_mock=true or legacy ?mock=true)
  const urlParams = new URLSearchParams(window.location.search)
  const mockFlag = urlParams.get('api_mock') ?? urlParams.get('mock')
  if (mockFlag === 'true') {
    // Persist mock mode to localStorage
    localStorage.setItem('slea_ssem_api_mock', 'true')
    return true
  }

  // Check localStorage (persists across page navigation)
  const storedMockFlag = localStorage.getItem('slea_ssem_api_mock')
  if (storedMockFlag === 'true') return true

  // Check environment variable
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
 * This allows tests to toggle mock mode (e.g., via localStorage) even
 * after modules have been imported.
 */
export const transport: HttpTransport = {
  get<T>(url: string, config) {
    return getTransport().get<T>(url, config)
  },
  post<T>(url: string, data, config) {
    return getTransport().post<T>(url, data, config)
  },
  put<T>(url: string, data, config) {
    return getTransport().put<T>(url, data, config)
  },
  delete<T>(url: string, config) {
    return getTransport().delete<T>(url, config)
  },
}

// Re-export types and utilities
export type { HttpTransport, RequestConfig } from './types'
export {
  setMockScenario,
  setMockData,
  mockConfig,
  getMockData,
  getMockRequests,
  clearMockRequests,
  setMockError,
  clearMockErrors,
  resetMockResults,
} from './mockTransport'
