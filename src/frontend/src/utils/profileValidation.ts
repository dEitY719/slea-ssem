/**
 * Profile Validation Utilities
 *
 * Provides validation functions for profile fields
 */

export interface NicknameValidationResult {
  isValid: boolean
  errorMessage: string | null
}

export interface CareerValidationResult {
  isValid: boolean
  errorMessage: string | null
}

export interface ProfileValidationResult {
  isValid: boolean
  errors: Record<string, string>
}

/**
 * Validate nickname field
 * @param nickname - Nickname to validate
 * @returns Validation result with error message if invalid
 */
export function validateNickname(nickname: string): NicknameValidationResult {
  if (!nickname || !nickname.trim()) {
    return {
      isValid: false,
      errorMessage: '닉네임을 입력해주세요.',
    }
  }

  return {
    isValid: true,
    errorMessage: null,
  }
}

/**
 * Validate career field (0-50 years)
 * @param career - Career years to validate
 * @returns Validation result with error message if invalid
 */
export function validateCareer(career: number): CareerValidationResult {
  if (career < 0 || career > 50) {
    return {
      isValid: false,
      errorMessage: '경력은 0~50 사이의 값을 입력해주세요.',
    }
  }

  return {
    isValid: true,
    errorMessage: null,
  }
}

/**
 * Validate level field (1-5)
 * @param level - Level to validate
 * @returns Validation result with error message if invalid
 */
export function validateLevel(level: number | null): ProfileValidationResult {
  const errors: Record<string, string> = {}

  if (level === null) {
    errors.level = '기술 수준을 선택해주세요.'
  } else if (level < 1 || level > 5) {
    errors.level = '유효하지 않은 기술 수준입니다.'
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  }
}

/**
 * Check if nickname needs validation (has changed)
 * @param currentNickname - Current nickname value
 * @param originalNickname - Original nickname value
 * @returns Whether duplicate check is needed
 */
export function shouldValidateNickname(
  currentNickname: string,
  originalNickname: string
): boolean {
  return currentNickname !== originalNickname
}

/**
 * Validate all required profile fields
 * @param data - Profile data to validate
 * @returns Validation result with all errors
 */
export interface ProfileData {
  nickname: string
  level: number | null
  career: number
  jobRole?: string
  duty?: string
  interests?: string
}

export function validateProfileData(data: ProfileData): ProfileValidationResult {
  const errors: Record<string, string> = {}

  // Validate nickname
  const nicknameResult = validateNickname(data.nickname)
  if (!nicknameResult.isValid && nicknameResult.errorMessage) {
    errors.nickname = nicknameResult.errorMessage
  }

  // Validate level
  const levelResult = validateLevel(data.level)
  if (!levelResult.isValid) {
    Object.assign(errors, levelResult.errors)
  }

  // Validate career
  const careerResult = validateCareer(data.career)
  if (!careerResult.isValid && careerResult.errorMessage) {
    errors.career = careerResult.errorMessage
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  }
}
