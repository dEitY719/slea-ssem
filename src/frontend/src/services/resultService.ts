// Result service - centralizes all test result-related API calls
// REQ: REQ-F-B4-1

import { transport } from '../lib/transport'

/**
 * Grade type (5-tier system)
 */
export type Grade = 'Beginner' | 'Intermediate' | 'Intermediate-Advanced' | 'Advanced' | 'Elite'

/**
 * Percentile confidence level
 */
export type PercentileConfidence = 'medium' | 'high'

/**
 * Grade distribution data (REQ: REQ-F-B4-3)
 */
export interface GradeDistribution {
  grade: Grade
  count: number
  percentage: number
}

/**
 * Test result data
 */
export interface GradeResult {
  user_id: number | string  // Backend returns string (knox_id)
  grade: Grade
  score: number // 0-100
  rank: number // 1-indexed
  total_cohort_size: number
  percentile: number // 0-100
  percentile_confidence: PercentileConfidence
  percentile_description: string // e.g., "상위 28%"
  grade_distribution?: GradeDistribution[] // REQ: REQ-F-B4-3 (Optional: Backend may not provide)
}

/**
 * Previous test result data (REQ: REQ-F-B5-1)
 */
export interface PreviousResult {
  grade: Grade
  score: number
  test_date: string // ISO date string
}

/**
 * Result service
 * Handles all test result-related API calls
 */
export const resultService = {
  /**
   * Get test results for a session
   *
   * REQ: REQ-F-B4-1
   *
   * @param sessionId - Test session ID (not used in API, kept for validation)
   * @returns Grade result with score, rank, percentile
   */
  async getResults(sessionId: string): Promise<GradeResult> {
    // Backend uses /profile/ranking (user-level, not session-level)
    // sessionId parameter kept for future extensibility
    return transport.get<GradeResult>('/api/profile/ranking')
  },

  /**
   * Get previous test result for comparison
   *
   * REQ: REQ-F-B5-1
   *
   * @returns Previous test result or null if first attempt
   */
  async getPreviousResult(): Promise<PreviousResult | null> {
    // TODO: Backend endpoint not yet implemented
    // For now, return null (no previous result available)
    return null
  },
}
