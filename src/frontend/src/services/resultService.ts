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
 * Test result data
 */
export interface GradeResult {
  user_id: number
  grade: Grade
  score: number // 0-100
  rank: number // 1-indexed
  total_cohort_size: number
  percentile: number // 0-100
  percentile_confidence: PercentileConfidence
  percentile_description: string // e.g., "상위 28%"
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
   * @param sessionId - Test session ID
   * @returns Grade result with score, rank, percentile
   */
  async getResults(sessionId: string): Promise<GradeResult> {
    return transport.get<GradeResult>(`/api/results/${sessionId}`)
  },
}
