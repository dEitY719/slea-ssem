// Question service - centralizes all question-related API calls
// REQ: REQ-F-B2-1, REQ-F-B2-6

import { transport } from '../lib/transport'

/**
 * Question type
 */
export type QuestionType = 'multiple_choice' | 'true_false' | 'short_answer'

/**
 * Question item
 */
export interface Question {
  id: string
  item_type: QuestionType
  stem: string
  choices: string[] | null
  difficulty: number
  category: string
}

/**
 * Generate questions request
 */
export interface GenerateQuestionsRequest {
  survey_id: string
  round?: number
  domain?: string
}

/**
 * Generate questions response
 */
export interface GenerateQuestionsResponse {
  session_id: string
  questions: Question[]
}

/**
 * Autosave request
 */
export interface AutosaveRequest {
  session_id: string
  question_id: string
  user_answer: string
  response_time_ms?: number
}

/**
 * Autosave response
 */
export interface AutosaveResponse {
  success: boolean
  message: string
  autosave_id: string
  saved_at: string
}

/**
 * Calculate score response
 */
export interface CalculateScoreResponse {
  session_id: string
  round: number
  score: number
  correct_count: number
  total_count: number
  wrong_categories: Record<string, number>
  auto_completed: boolean
}

/**
 * Question service
 * Handles all question-related API calls
 */
export const questionService = {
  /**
   * Generate test questions based on user profile
   *
   * @param request - Question generation request
   * @returns Session ID and generated questions
   */
  async generateQuestions(
    request: GenerateQuestionsRequest
  ): Promise<GenerateQuestionsResponse> {
    return transport.post<GenerateQuestionsResponse>('/api/questions/generate', request)
  },

  /**
   * Autosave user answer
   *
   * @param autosaveData - Answer data to save
   * @returns Autosave response
   */
  async autosave(autosaveData: AutosaveRequest): Promise<AutosaveResponse> {
    return transport.post<AutosaveResponse>('/api/questions/autosave', autosaveData)
  },

  /**
   * Calculate round score and auto-complete session
   *
   * REQ: REQ-B-B3-Score
   *
   * @param sessionId - Test session ID
   * @param autoComplete - Whether to auto-complete session if all answers scored (default true)
   * @returns Score result with auto_completed status
   */
  async calculateScore(
    sessionId: string,
    autoComplete: boolean = true
  ): Promise<CalculateScoreResponse> {
    return transport.post<CalculateScoreResponse>(
      `/api/questions/score?session_id=${sessionId}&auto_complete=${autoComplete}`,
      {}
    )
  },
}
