/**
 * Profile Level Constants
 *
 * Shared across:
 * - SignupPage (REQ-F-A2-Signup-4)
 * - ProfileSetupPage (REQ-F-A2-2-2)
 * - ProfileEditPage (future)
 *
 * Level mapping:
 * 1 - Beginner: 입문 - 기초 개념 학습 중
 * 2 - Intermediate: 초급 - 기본 업무 수행 가능
 * 3 - Intermediate-Advanced: 중급 - 독립적으로 업무 수행
 * 4 - Advanced: 고급 - 복잡한 문제 해결 가능
 * 5 - Elite: 전문가 - 다른 사람을 지도 가능
 */

export type LevelOption = {
  value: number
  label: string
  description: string
}

export const LEVEL_OPTIONS: LevelOption[] = [
  { value: 1, label: '1 - 입문', description: '기초 개념 학습 중' },
  { value: 2, label: '2 - 초급', description: '기본 업무 수행 가능' },
  { value: 3, label: '3 - 중급', description: '독립적으로 업무 수행' },
  { value: 4, label: '4 - 고급', description: '복잡한 문제 해결 가능' },
  { value: 5, label: '5 - 전문가', description: '다른 사람을 지도 가능' },
] as const

/**
 * Level number to backend string mapping
 *
 * Used for API requests to convert frontend number values
 * to backend enum strings.
 *
 * Backend only accepts: 'beginner', 'intermediate', 'advanced'
 * Frontend levels 1-5 are mapped to these 3 backend levels.
 *
 * Reused in:
 * - SignupPage (REQ-F-A2-Signup-6)
 * - SelfAssessmentPage (REQ-F-A2-2-2)
 * - ProfileEditPage (future)
 * - Any page that submits profile data
 */
export const LEVEL_MAPPING: Record<number, string> = {
  1: 'beginner',
  2: 'intermediate',
  3: 'intermediate',
  4: 'advanced',
  5: 'advanced',
}
