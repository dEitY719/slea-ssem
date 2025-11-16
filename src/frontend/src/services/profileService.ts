// Profile service - centralizes all profile-related API calls
// REQ: REQ-F-A2-1, REQ-F-A2-2, REQ-F-A2-3

import { transport } from '../lib/transport'

/**
 * User profile response from GET /api/profile/nickname
 */
export interface UserProfileResponse {
  user_id: string
  nickname: string | null
  registered_at: string | null
  updated_at: string | null
}

/**
 * Nickname check request
 */
export interface NicknameCheckRequest {
  nickname: string
}

/**
 * Nickname check response
 */
export interface NicknameCheckResponse {
  available: boolean
  suggestions: string[]
}

/**
 * Nickname register request
 */
export interface NicknameRegisterRequest {
  nickname: string
}

/**
 * Nickname register response
 */
export interface NicknameRegisterResponse {
  success: boolean
  message: string
  user_id: string
  nickname: string
  registered_at: string
}

/**
 * Survey update request
 */
export interface SurveyUpdateRequest {
  level: string
  career: number
  interests: string[]
}

/**
 * Survey update response
 */
export interface SurveyUpdateResponse {
  survey_id: string
}

/**
 * Profile service
 * Handles all profile-related API calls
 */
export const profileService = {
  /**
   * Get current user's nickname information
   *
   * @returns User profile with nickname info
   */
  async getNickname(): Promise<UserProfileResponse> {
    return transport.get<UserProfileResponse>('/api/profile/nickname')
  },

  /**
   * Check if nickname is available
   *
   * @param nickname - Nickname to check
   * @returns Availability status and suggestions
   */
  async checkNickname(nickname: string): Promise<NicknameCheckResponse> {
    return transport.post<NicknameCheckResponse>('/api/profile/nickname/check', {
      nickname,
    })
  },

  /**
   * Register nickname for current user
   *
   * @param nickname - Nickname to register
   * @returns Registration response
   */
  async registerNickname(nickname: string): Promise<NicknameRegisterResponse> {
    return transport.post<NicknameRegisterResponse>('/api/profile/register', {
      nickname,
    })
  },

  /**
   * Update user profile survey
   *
   * @param surveyData - Survey data (level, career, interests)
   * @returns Survey update response with survey_id
   */
  async updateSurvey(surveyData: SurveyUpdateRequest): Promise<SurveyUpdateResponse> {
    return transport.put<SurveyUpdateResponse>('/api/profile/survey', surveyData)
  },

}
