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
 * Note: Only level and career are required, other fields are optional (can be null)
 */
export interface SurveyUpdateRequest {
  level: string
  career: number
  job_role: string | null
  duty: string | null
  interests: string[] | null
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
 * Profile history response - REQ: REQ-F-B5-Retake-1
 * Returns user's previous assessment data for retake
 */
export interface ProfileHistoryResponse {
  nickname: string
  survey: {
    survey_id: string
    level: string
    career: number
    job_role: string
    duty: string
    interests: string[]
  }
  last_test_date: string | null
}

/**
 * Profile service
 * Handles all profile-related API calls
 */
export const profileService = {
  /**
   * Get current user's nickname information
   * REQ-B-A0-API: Private-Auth API (SSO required, but signup not required)
   *
   * @returns User profile with nickname info
   */
  async getNickname(): Promise<UserProfileResponse> {
    return transport.get<UserProfileResponse>('/api/profile/nickname', {
      accessLevel: 'private-auth'
    })
  },

  /**
   * Check if nickname is available
   * REQ-B-A0-API: Private-Auth API (SSO required, but signup not required)
   *
   * @param nickname - Nickname to check
   * @returns Availability status and suggestions
   */
  async checkNickname(nickname: string): Promise<NicknameCheckResponse> {
    return transport.post<NicknameCheckResponse>('/api/profile/nickname/check', {
      nickname,
    }, {
      accessLevel: 'private-auth'
    })
  },

  /**
   * Register nickname for current user
   * REQ-B-A0-API: Private-Auth API (SSO required, but signup not required)
   *
   * @param nickname - Nickname to register
   * @returns Registration response
   */
  async registerNickname(nickname: string): Promise<NicknameRegisterResponse> {
    return transport.post<NicknameRegisterResponse>('/api/profile/register', {
      nickname,
    }, {
      accessLevel: 'private-auth'
    })
  },

  /**
   * Get user profile survey data
   * REQ-B-A0-API: Private-Auth API (SSO required, but signup not required)
   *
   * @returns Survey data with level, career, job_role, duty, interests
   */
  async getSurvey(): Promise<SurveyDataResponse> {
    return transport.get<SurveyDataResponse>('/api/profile/survey', {
      accessLevel: 'private-auth'
    })
  },

  /**
   * Update user profile survey
   * REQ-B-A0-API: Private-Auth API (SSO required, but signup not required)
   *
   * @param surveyData - Survey data (level, career, interests)
   * @returns Survey update response with survey_id
   */
  async updateSurvey(surveyData: SurveyUpdateRequest): Promise<SurveyUpdateResponse> {
    return transport.put<SurveyUpdateResponse>('/api/profile/survey', surveyData, {
      accessLevel: 'private-auth'
    })
  },

  /**
   * Get current user's privacy consent status
   * REQ-B-A0-API: Private-Auth API (SSO required, but signup not required)
   *
   * REQ: REQ-F-A3-5
   *
   * @returns Consent status with timestamp
   */
  async getConsentStatus(): Promise<ConsentStatusResponse> {
    return transport.get<ConsentStatusResponse>('/api/profile/consent', {
      accessLevel: 'private-auth'
    })
  },

  /**
   * Update current user's privacy consent status
   * REQ-B-A0-API: Private-Auth API (SSO required, but signup not required)
   *
   * REQ: REQ-F-A3-5
   *
   * @param consent - Consent status (true to grant, false to withdraw)
   * @returns Consent update response
   */
  async updateConsent(consent: boolean): Promise<ConsentUpdateResponse> {
    return transport.post<ConsentUpdateResponse>('/api/profile/consent', { consent }, {
      accessLevel: 'private-auth'
    })
  },

  /**
   * Get user's profile history for retake
   *
   * REQ: REQ-F-B5-Retake-1
   * Returns previous assessment data to auto-fill retake form
   *
   * @returns Profile history with survey data and last test date
   */
  async getProfileHistory(): Promise<ProfileHistoryResponse> {
    return transport.get<ProfileHistoryResponse>('/api/profile/history')
  },

}
