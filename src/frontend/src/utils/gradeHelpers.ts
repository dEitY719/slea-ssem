// REQ: REQ-F-B4-1, REQ-F-B4-2
/**
 * Unified Grade utility functions
 *
 * Provides conversion and utility functions for all grade/level representations:
 * - Frontend Level (1-5 numeric)
 * - Backend Level ("beginner", "intermediate", "advanced")
 * - Grade String ("Beginner", "Elite", etc.)
 * - Korean translations
 * - CSS classes
 */

import { GRADE_CONFIG, GRADE_STRING_TO_LEVEL, ELITE_GRADE_LEVEL } from '../constants/gradeConfig'
import type { FrontendLevel, GradeString, GradeInfo } from '../types/grade'

/**
 * ============================================================================
 * Type Guards
 * ============================================================================
 */

/**
 * Type guard to check if a string is a valid GradeString
 * @param value - String to check
 * @returns true if value is a valid GradeString
 */
export const isGradeString = (value: string): value is GradeString => {
  return value in GRADE_STRING_TO_LEVEL
}

/**
 * ============================================================================
 * Internal Helper Functions (Single Source of Truth)
 * ============================================================================
 */

/**
 * Validate and normalize a level to FrontendLevel
 * @internal
 * @param level - Level to validate
 * @returns Valid FrontendLevel or null
 */
const getValidLevel = (level: FrontendLevel | number | null | undefined): FrontendLevel | null => {
  if (!level || level < 1 || level > 5) return null
  return level as FrontendLevel
}

/**
 * Get grade config for a level with validation
 * @internal
 * @param level - Level to get config for
 * @returns GradeInfo or null if invalid
 */
const getGradeConfig = (level: FrontendLevel | number | null | undefined): GradeInfo | null => {
  const validLevel = getValidLevel(level)
  if (!validLevel) return null
  return GRADE_CONFIG[validLevel]
}

/**
 * Convert grade string to frontend level with validation
 * @internal
 * @param grade - Grade string to convert
 * @returns Frontend level or null if invalid
 */
const getLevelFromGrade = (grade: string): FrontendLevel | null => {
  if (!isGradeString(grade)) return null
  return GRADE_STRING_TO_LEVEL[grade]
}

/**
 * ============================================================================
 * Level → Other conversions (from numeric level 1-5)
 * ============================================================================
 */

/**
 * Convert frontend level (1-5) to Korean text
 * @param level - Frontend level (1-5) or null/undefined
 * @returns Korean text representation or fallback
 */
export const getLevelKorean = (level: FrontendLevel | number | null | undefined): string => {
  const config = getGradeConfig(level)
  return config?.korean ?? '정보 없음'
}

/**
 * Convert frontend level (1-5) to grade string
 * @param level - Frontend level (1-5) or null/undefined
 * @returns Grade string (e.g., "Elite", "Beginner") or fallback
 */
export const getLevelGradeString = (level: FrontendLevel | number | null | undefined): string => {
  const config = getGradeConfig(level)
  return config?.gradeString ?? 'Unknown'
}

/**
 * Convert frontend level (1-5) to CSS class
 * @param level - Frontend level (1-5) or null/undefined
 * @returns CSS class name
 */
export const getLevelClass = (level: FrontendLevel | number | null | undefined): string => {
  const config = getGradeConfig(level)
  return config?.cssClass ?? 'grade-default'
}

/**
 * Convert frontend level (1-5) to description text
 * @param level - Frontend level (1-5) or null/undefined
 * @returns Description text
 */
export const getLevelDescription = (level: FrontendLevel | number | null | undefined): string => {
  const config = getGradeConfig(level)
  return config?.description ?? '정보 없음'
}

/**
 * ============================================================================
 * Grade String → Other conversions (from "Elite", "Beginner", etc.)
 * ============================================================================
 */

/**
 * Convert English grade to Korean
 * @param grade - Grade string (e.g., "Elite", "Beginner")
 * @returns Korean text (returns input if invalid grade)
 */
export const getGradeKorean = (grade: string): string => {
  const level = getLevelFromGrade(grade)
  if (!level) return grade // Fallback for invalid grades
  return GRADE_CONFIG[level].korean
}

/**
 * Get grade CSS class for color coding
 * @param grade - Grade string (e.g., "Elite", "Beginner")
 * @returns CSS class name
 */
export const getGradeClass = (grade: string): string => {
  const level = getLevelFromGrade(grade)
  if (!level) return 'grade-default' // Fallback for invalid grades
  return GRADE_CONFIG[level].cssClass
}

/**
 * Convert grade string to frontend level
 * @param grade - Grade string (e.g., "Elite", "Beginner")
 * @returns Frontend level (1-5) or null if invalid
 */
export const getGradeLevel = (grade: string): number | null => {
  return getLevelFromGrade(grade)
}

/**
 * ============================================================================
 * Special checks
 * ============================================================================
 */

/**
 * Check if grade is Elite
 *
 * REQ: REQ-F-B4-2 - Elite 등급 확인하여 특수 배지 표시
 * @param grade - Grade string OR numeric level
 * @returns true if Elite grade
 */
export const isEliteGrade = (grade: string | number): boolean => {
  if (typeof grade === 'number') {
    return grade === ELITE_GRADE_LEVEL
  }
  // Use type guard for string grades
  return isGradeString(grade) && grade === 'Elite'
}

/**
 * ============================================================================
 * Utility functions
 * ============================================================================
 */

/**
 * Format decimal - remove trailing zero for integers
 * Examples: 85.0 -> "85", 87.5 -> "87.5"
 * @param value - Numeric value
 * @returns Formatted string
 */
export const formatDecimal = (value: number): string => {
  return Number(value.toFixed(1)).toString()
}
