// Custom hook for autosaving test answers
// REQ: REQ-F-B2-6

import { useEffect, useState } from 'react'
import { questionService } from '../services'
import type { QuestionData } from '../components/test/Question'

export type SaveStatusType = 'idle' | 'saving' | 'saved' | 'error'

interface UseAutosaveOptions {
  sessionId: string | null
  currentQuestion: QuestionData | null
  answer: string
  questionStartTime: number
  debounceMs?: number
}

interface UseAutosaveResult {
  saveStatus: SaveStatusType
  lastSavedAnswer: string
}

/**
 * Custom hook for autosaving test answers
 *
 * REQ: REQ-F-B2-6 - Autosave with visual feedback
 *
 * Features:
 * - Debounced autosave (default 1 second)
 * - Prevents duplicate saves
 * - Visual status feedback
 * - Error handling
 *
 * @param options - Autosave configuration
 * @returns Save status and last saved answer
 */
export function useAutosave({
  sessionId,
  currentQuestion,
  answer,
  questionStartTime,
  debounceMs = 1000,
}: UseAutosaveOptions): UseAutosaveResult {
  const [saveStatus, setSaveStatus] = useState<SaveStatusType>('idle')
  const [lastSavedAnswer, setLastSavedAnswer] = useState<string>('')

  useEffect(() => {
    // Only autosave if answer is not empty, different from last saved, and session is ready
    if (
      !answer.trim() ||
      answer === lastSavedAnswer ||
      !sessionId ||
      !currentQuestion
    ) {
      return
    }

    const timer = setTimeout(async () => {
      setSaveStatus('saving')
      try {
        // Build user_answer based on question type
        let userAnswer: { selected?: string; text?: string }
        if (
          currentQuestion.item_type === 'multiple_choice' ||
          currentQuestion.item_type === 'true_false'
        ) {
          userAnswer = { selected: answer }
        } else {
          userAnswer = { text: answer }
        }

        await questionService.autosave({
          session_id: sessionId,
          question_id: currentQuestion.id,
          user_answer: JSON.stringify(userAnswer),
        })

        setLastSavedAnswer(answer)
        setSaveStatus('saved')

        // Hide "저장됨" message after 2 seconds
        setTimeout(() => setSaveStatus('idle'), 2000)
      } catch (err) {
        console.error('Autosave error:', err)
        setSaveStatus('error')
      }
    }, debounceMs)

    return () => clearTimeout(timer)
  }, [answer, sessionId, currentQuestion, questionStartTime, lastSavedAnswer, debounceMs])

  return { saveStatus, lastSavedAnswer }
}
