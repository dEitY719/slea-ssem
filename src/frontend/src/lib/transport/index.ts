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
 * Default transport instance
 * Import this in your hooks/components
 */
export const transport = getTransport()

// Re-export types and utilities
export type { HttpTransport, RequestConfig } from './types'
export { setMockScenario, setMockData, mockConfig } from './mockTransport'
