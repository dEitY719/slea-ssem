// REQ: REQ-F-B4-1
/**
 * Grade utility functions for TestResultsPage
 */

/**
 * Convert English grade to Korean
 */
export const getGradeKorean = (grade: string): string => {
  const gradeMap: Record<string, string> = {
    Beginner: '시작자',
    Intermediate: '중급자',
    'Intermediate-Advanced': '중상급자',
    Advanced: '고급자',
    Elite: '엘리트',
  }
  return gradeMap[grade] || grade
}

/**
 * Get grade CSS class for color coding
 */
export const getGradeClass = (grade: string): string => {
  const classMap: Record<string, string> = {
    Beginner: 'grade-beginner',
    Intermediate: 'grade-intermediate',
    'Intermediate-Advanced': 'grade-intermediate-advanced',
    Advanced: 'grade-advanced',
    Elite: 'grade-elite',
  }
  return classMap[grade] || 'grade-default'
}

/**
 * Format decimal - remove trailing zero for integers
 * Examples: 85.0 -> "85", 87.5 -> "87.5"
 */
export const formatDecimal = (value: number): string => {
  return Number(value.toFixed(1)).toString()
}
