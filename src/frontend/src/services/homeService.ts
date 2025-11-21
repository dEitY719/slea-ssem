// REQ: REQ-F-A1-Home
import { transport } from '../lib/transport'

/**
 * Last Test Result Response
 * REQ: REQ-F-A1-Home-1, REQ-F-A1-Home-2, REQ-F-A1-Home-3
 */
export interface LastTestResult {
  hasResult: boolean
  grade: number | null // 1~5
  completedAt: string | null // YYYY-MM-DD
  badgeUrl: string | null
}

/**
 * Total Participants Response
 * REQ: REQ-F-A1-Home-4
 */
export interface StatisticsResponse {
  totalParticipants: number
}

/**
 * Get last test result for current user
 * REQ: REQ-F-A1-Home-1
 */
export const getLastTestResult = async (): Promise<LastTestResult> => {
  return await transport.get<LastTestResult>('/api/profile/last-test-result')
}

/**
 * Get total test participants count
 * REQ: REQ-F-A1-Home-4
 */
export const getTotalParticipants = async (): Promise<StatisticsResponse> => {
  return await transport.get<StatisticsResponse>('/api/statistics/total-participants')
}

/**
 * Get badge label for grade
 * REQ: REQ-F-A1-Home-3
 */
export const getBadgeLabel = (grade: number | null): string => {
  if (!grade) return ''
  switch (grade) {
    case 1:
      return 'Beginner'
    case 2:
      return 'Elementary'
    case 3:
      return 'Intermediate'
    case 4:
      return 'Advanced'
    case 5:
      return 'Expert'
    default:
      return ''
  }
}

export const homeService = {
  getLastTestResult,
  getTotalParticipants,
  getBadgeLabel,
}
