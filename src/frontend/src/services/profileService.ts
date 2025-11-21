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
  job_role: string
  duty: string
  interests: string[]
}

/**
 * Survey data response from GET /api/profile/survey
 */
export interface SurveyDataResponse {
  level: string | null
  career: number | null
  job_role: string | null
  duty: string | null
  interests: string[] | null
}

/**
 * Survey update response
 */
export interface SurveyUpdateResponse {
  survey_id: string
}

/**
 * Consent status response - REQ: REQ-F-A3
 */
export interface ConsentStatusResponse {
  consented: boolean
  consent_at: string | null
}

/**
 * Consent update request - REQ: REQ-F-A3
 */
export interface ConsentUpdateRequest {
  consent: boolean
}

/**
 * Consent update response - REQ: REQ-F-A3
 */
export interface ConsentUpdateResponse {
  message: string
  consented: boolean
  consent_at: string | null
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
   * Get user profile survey data
   *
   * @returns Survey data with level, career, job_role, duty, interests
   */
  async getSurvey(): Promise<SurveyDataResponse> {
    return transport.get<SurveyDataResponse>('/api/profile/survey')
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

  /**
   * Get current user's privacy consent status
   *
   * REQ: REQ-F-A3-5
   *
   * @returns Consent status with timestamp
   */
  async getConsentStatus(): Promise<ConsentStatusResponse> {
    return transport.get<ConsentStatusResponse>('/api/profile/consent')
  },

  /**
   * Update current user's privacy consent status
   *
   * REQ: REQ-F-A3-5
   *
   * @param consent - Consent status (true to grant, false to withdraw)
   * @returns Consent update response
   */
  async updateConsent(consent: boolean): Promise<ConsentUpdateResponse> {
    return transport.post<ConsentUpdateResponse>('/api/profile/consent', { consent })
  },

}
