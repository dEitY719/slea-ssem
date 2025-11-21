/**
 * Level Mapping Utilities
 *
 * Converts between frontend (1-5 scale) and backend (beginner/intermediate/advanced) level values
 */

export type BackendLevel = 'beginner' | 'intermediate' | 'advanced'
export type FrontendLevel = 1 | 2 | 3 | 4 | 5

/**
 * Frontend to Backend level mapping
 * 1 → beginner
 * 2-3 → intermediate
 * 4-5 → advanced
 */
const LEVEL_TO_BACKEND: Record<number, BackendLevel> = {
  1: 'beginner',
  2: 'intermediate',
  3: 'intermediate',
  4: 'advanced',
  5: 'advanced',
}

/**
 * Backend to Frontend level mapping (reverse)
 * beginner → 1
 * intermediate → 2 (default middle value)
 * advanced → 4 (default middle value)
 */
const BACKEND_TO_LEVEL: Record<BackendLevel, number> = {
  beginner: 1,
  intermediate: 2,
  advanced: 4,
}

/**
 * Convert frontend level (1-5) to backend level string
 * @param level - Frontend level (1-5)
 * @returns Backend level string (beginner/intermediate/advanced)
 * @throws Error if level is not in valid range
 */
export function levelToBackend(level: number): BackendLevel {
  if (level < 1 || level > 5) {
    throw new Error(`Invalid level: ${level}. Must be between 1 and 5.`)
  }
  return LEVEL_TO_BACKEND[level]
}

/**
 * Convert backend level string to frontend level (1-5)
 * @param backendLevel - Backend level string (beginner/intermediate/advanced)
 * @returns Frontend level number (1-5)
 * @throws Error if backendLevel is not valid
 */
export function backendToLevel(backendLevel: string): number {
  const normalized = backendLevel.toLowerCase() as BackendLevel

  if (!BACKEND_TO_LEVEL[normalized]) {
    throw new Error(`Invalid backend level: ${backendLevel}. Must be one of: beginner, intermediate, advanced.`)
  }

  return BACKEND_TO_LEVEL[normalized]
}

/**
 * Safely convert backend level string to frontend level with fallback
 * @param backendLevel - Backend level string (can be null/undefined)
 * @returns Frontend level number (1-5) or null if invalid
 */
export function safeBackendToLevel(backendLevel: string | null | undefined): number | null {
  if (!backendLevel) {
    return null
  }

  try {
    return backendToLevel(backendLevel)
  } catch {
    return null
  }
}
