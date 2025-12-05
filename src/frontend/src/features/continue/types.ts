// Continue flow types
// Purpose: Define common types for continue intent handlers

/**
 * Intent types for continue flow
 */
export type ContinueIntent = 'service_login' | 'leveltest'

/**
 * Context passed to intent handlers
 */
export interface ContinueContext {
  navigate: (path: string, options?: { replace?: boolean }) => void
  /**
   * Optional destination to resume original intent (e.g., /test/start)
   */
  returnTo?: string
}
