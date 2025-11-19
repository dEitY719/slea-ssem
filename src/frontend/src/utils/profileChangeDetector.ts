/**
 * Profile Change Detector Utilities
 *
 * Detects changes in profile data to enable conditional API calls
 */

export interface ProfileFormData {
  nickname: string
  level: number | null
  career: number
  jobRole: string
  duty: string
  interests: string
}

export interface OriginalProfileData {
  nickname: string
  level: number | null
  career: number
  jobRole: string
  duty: string
  interests: string
}

export interface ChangeDetectionResult {
  hasChanges: boolean
  nicknameChanged: boolean
  surveyDataChanged: boolean
  changedFields: string[]
}

/**
 * Detect what fields have changed in profile data
 * @param current - Current form data
 * @param original - Original data from server
 * @returns Change detection result
 */
export function detectProfileChanges(
  current: ProfileFormData,
  original: OriginalProfileData
): ChangeDetectionResult {
  const changedFields: string[] = []

  // Check nickname change
  const nicknameChanged = current.nickname !== original.nickname
  if (nicknameChanged) {
    changedFields.push('nickname')
  }

  // Check survey data changes
  const levelChanged = current.level !== original.level
  const careerChanged = current.career !== original.career
  const jobRoleChanged = current.jobRole !== original.jobRole
  const dutyChanged = current.duty !== original.duty
  const interestsChanged = current.interests !== original.interests

  const surveyDataChanged =
    levelChanged || careerChanged || jobRoleChanged || dutyChanged || interestsChanged

  if (levelChanged) changedFields.push('level')
  if (careerChanged) changedFields.push('career')
  if (jobRoleChanged) changedFields.push('jobRole')
  if (dutyChanged) changedFields.push('duty')
  if (interestsChanged) changedFields.push('interests')

  return {
    hasChanges: nicknameChanged || surveyDataChanged,
    nicknameChanged,
    surveyDataChanged,
    changedFields,
  }
}

/**
 * Check if only specific fields changed
 * @param changes - Change detection result
 * @param fields - Fields to check
 * @returns Whether only specified fields changed
 */
export function onlyFieldsChanged(
  changes: ChangeDetectionResult,
  fields: string[]
): boolean {
  const changedSet = new Set(changes.changedFields)
  const targetSet = new Set(fields)

  return (
    changedSet.size === targetSet.size &&
    Array.from(changedSet).every((field) => targetSet.has(field))
  )
}
