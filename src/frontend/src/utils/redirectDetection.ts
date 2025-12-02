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
 * Check if redirect loop is detected and update counter
 * REQ: REQ-F-A1-Error-1
 *
 * @returns RedirectDetectionResult - shouldShowError: true if >= 3 redirects in 5 min
 */
export function detectRedirectLoop(): RedirectDetectionResult {
  const count = Number(localStorage.getItem(REDIRECT_COUNT_KEY) || 0) + 1
  const lastTimestamp = Number(localStorage.getItem(REDIRECT_TIMESTAMP_KEY) || 0)
  const now = Date.now()

  // Reset counter if time window expired
  if (now - lastTimestamp >= TIME_WINDOW_MS) {
    localStorage.setItem(REDIRECT_COUNT_KEY, '1')
    localStorage.setItem(REDIRECT_TIMESTAMP_KEY, String(now))
    return { shouldShowError: false, count: 1 }
  }

  // Update counter
  localStorage.setItem(REDIRECT_COUNT_KEY, String(count))
  localStorage.setItem(REDIRECT_TIMESTAMP_KEY, String(now))

  // Check if threshold exceeded
  const shouldShowError = count >= REDIRECT_THRESHOLD

  return { shouldShowError, count }
}

/**
 * Reset redirect detection counter
 * Call this when user successfully authenticates or clicks "Try Again"
 */
export function resetRedirectDetection(): void {
  localStorage.removeItem(REDIRECT_COUNT_KEY)
  localStorage.removeItem(REDIRECT_TIMESTAMP_KEY)
}
