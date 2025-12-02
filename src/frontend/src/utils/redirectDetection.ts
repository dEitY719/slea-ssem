// REQ: REQ-F-A1-Error-1 - Detect infinite redirect loop

const REDIRECT_COUNT_KEY = 'auth_redirect_count'
const REDIRECT_TIMESTAMP_KEY = 'auth_redirect_timestamp'
const REDIRECT_THRESHOLD = 3
const TIME_WINDOW_MS = 5 * 60 * 1000 // 5 minutes

export interface RedirectDetectionResult {
  shouldShowError: boolean
  count: number
}

/**
 * Safe sessionStorage getter with fallback
 */
function getStorageItem(key: string): string | null {
  try {
    return sessionStorage.getItem(key)
  } catch (error) {
    console.warn('[RedirectDetection] sessionStorage not available:', error)
    return null
  }
}

/**
 * Safe sessionStorage setter with fallback
 */
function setStorageItem(key: string, value: string): void {
  try {
    sessionStorage.setItem(key, value)
  } catch (error) {
    console.warn('[RedirectDetection] sessionStorage not available:', error)
  }
}

/**
 * Safe sessionStorage remover with fallback
 */
function removeStorageItem(key: string): void {
  try {
    sessionStorage.removeItem(key)
  } catch (error) {
    console.warn('[RedirectDetection] sessionStorage not available:', error)
  }
}

/**
 * Check if redirect loop is detected and update counter
 * REQ: REQ-F-A1-Error-1
 *
 * Uses sessionStorage (tab-scoped, survives page reload/IDP redirect)
 *
 * @returns RedirectDetectionResult - shouldShowError: true if >= 3 redirects in 5 min
 */
export function detectRedirectLoop(): RedirectDetectionResult {
  const count = Number(getStorageItem(REDIRECT_COUNT_KEY) || 0) + 1
  const lastTimestamp = Number(getStorageItem(REDIRECT_TIMESTAMP_KEY) || 0)
  const now = Date.now()

  // Reset counter if time window expired
  if (now - lastTimestamp >= TIME_WINDOW_MS) {
    setStorageItem(REDIRECT_COUNT_KEY, '1')
    setStorageItem(REDIRECT_TIMESTAMP_KEY, String(now))
    return { shouldShowError: false, count: 1 }
  }

  // Update counter
  setStorageItem(REDIRECT_COUNT_KEY, String(count))
  setStorageItem(REDIRECT_TIMESTAMP_KEY, String(now))

  // Check if threshold exceeded
  const shouldShowError = count >= REDIRECT_THRESHOLD

  return { shouldShowError, count }
}

/**
 * Reset redirect detection counter
 * Call this when user successfully authenticates or clicks "Try Again"
 */
export function resetRedirectDetection(): void {
  removeStorageItem(REDIRECT_COUNT_KEY)
  removeStorageItem(REDIRECT_TIMESTAMP_KEY)
}
