/**
 * Shared types for profile-related retake flows (REQ-F-B5-Retake-1)
 */
export interface RetakeProfileData {
  surveyId: string
  level: string
  career: number
  jobRole: string
  duty: string
  interests: string[]
}

export interface RetakeLocationState {
  retakeMode?: boolean
  profileData?: RetakeProfileData
}
