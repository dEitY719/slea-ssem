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
    return transport.post<GenerateQuestionsResponse>('/questions/generate', request)
  },

  /**
   * Autosave user answer
   *
   * @param autosaveData - Answer data to save
   * @returns Autosave response
   */
  async autosave(autosaveData: AutosaveRequest): Promise<AutosaveResponse> {
    return transport.post<AutosaveResponse>('/questions/autosave', autosaveData)
  },
}
