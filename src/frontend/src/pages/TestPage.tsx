// REQ: REQ-F-B2-1, REQ-F-B2-2, REQ-F-B2-6
import React, { useEffect, useState, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { ArrowRightIcon, ArrowLeftIcon, CheckIcon } from '@heroicons/react/24/outline'
import { questionService } from '../services'
import { Timer, SaveStatus, Question, type QuestionData, type SaveStatusType } from '../components/test'
import './TestPage.css'

/**
 * Test Page Component
 *
 * REQ: REQ-F-B2-1 - 생성된 문항을 순차적으로 표시
 * REQ: REQ-F-B2-2 - 진행률, 응답 입력, "다음" 버튼, 타이머 제공
 * REQ: REQ-F-B2-6 - "다음" 버튼 클릭 시 저장 with visual feedback
 *
 * Features:
 * - Generate test questions on mount
 * - Display questions one by one
 * - Timer (20 minutes)
 * - Save answers on "Next" button click
 * - Submit and navigate to results
 *
 * Route: /test
 */

type LocationState = {
  surveyId: string
  round: number
}

const TestPage: React.FC = () => {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [questions, setQuestions] = useState<QuestionData[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answer, setAnswer] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [loadingError, setLoadingError] = useState<string | null>(null)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [questionStartTime, setQuestionStartTime] = useState<number>(Date.now())
  const [timeRemaining, setTimeRemaining] = useState<number>(1200) // 20 minutes = 1200 seconds
  const [saveStatus, setSaveStatus] = useState<SaveStatusType>('idle') // REQ-F-B2-6: Save status management

  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as LocationState

  // Get current question
  const currentQuestion = questions[currentIndex] || null

  // Load questions on mount
  useEffect(() => {
    // Prevent duplicate calls (React Strict Mode calls useEffect twice in dev)
    let cancelled = false

    const generateQuestions = async () => {
      if (!state?.surveyId) {
        setLoadingError('자기평가 정보가 없습니다. 프로필 리뷰 페이지로 돌아가주세요.')
        setIsLoading(false)
        return
      }

      // Skip if already loaded (prevents StrictMode double-call issue)
      if (sessionId && questions.length > 0) {
        setIsLoading(false)
        return
      }

      setIsLoading(true)
      setLoadingError(null)

      try {
        const response = await questionService.generateQuestions({
          survey_id: state.surveyId,
          round: state.round || 1,
          domain: 'AI',
        })

        // Only update state if not cancelled
        if (!cancelled) {
          setSessionId(response.session_id)
          setQuestions(response.questions)
          setQuestionStartTime(Date.now())
          setIsLoading(false)
        }
      } catch (err) {
        if (!cancelled) {
          const message =
            err instanceof Error
              ? err.message
              : '문제 생성에 실패했습니다. 다시 시도해주세요.'
          setLoadingError(message)
          setIsLoading(false)
        }
      }
    }

    generateQuestions()

    // Cleanup function to prevent state updates after unmount
    return () => {
      cancelled = true
    }
  }, [state?.surveyId, state?.round, sessionId, questions.length])

  // Reset state when moving to next question
  useEffect(() => {
    setQuestionStartTime(Date.now())
    setSubmitError(null)
    setAnswer('')
    setSaveStatus('idle') // Reset save status for new question
  }, [currentIndex])

  // Timer countdown logic (REQ-F-B2-2, REQ-F-B2-5)
  useEffect(() => {
    if (!sessionId || questions.length === 0) return

    const interval = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 0) {
          clearInterval(interval)
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(interval)
  }, [sessionId, questions])

  // Handle next button click
  const handleNextClick = useCallback(async () => {
    if (!sessionId || !answer.trim() || isSubmitting) {
      return
    }

    // REQ-F-B2-6: Show "저장 중..." when saving
    setSaveStatus('saving')
    setIsSubmitting(true)
    setSubmitError(null)

    try {
      const currentQuestion = questions[currentIndex]

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

      // Submit answer to backend
        const responseTime = Date.now() - questionStartTime
        await questionService.autosave({
        session_id: sessionId,
        question_id: currentQuestion.id,
          user_answer: JSON.stringify(userAnswer),
          response_time_ms: responseTime,
      })

      // REQ-F-B2-6: Show "저장됨" after successful save
      setSaveStatus('saved')

      // Hide "저장됨" message after 2 seconds
      setTimeout(() => setSaveStatus('idle'), 2000)

      // Move to next question or finish
      if (currentIndex < questions.length - 1) {
        setCurrentIndex(currentIndex + 1)
        setAnswer('')
        setIsSubmitting(false)
      } else {
        // All questions answered, navigate to results
        navigate('/test-results', { state: { sessionId, surveyId: state.surveyId } })
      }
    } catch (err) {
      const message =
        err instanceof Error ? err.message : '답변 제출에 실패했습니다.'

      // REQ-F-B2-6: Show "저장 실패" on error
      setSaveStatus('error')
      setSubmitError(message)
      setIsSubmitting(false)
    }
  }, [sessionId, answer, isSubmitting, currentIndex, questions, questionStartTime, navigate, state.surveyId])

  // Loading state
  if (isLoading) {
    return (
      <main className="test-page">
        <div className="test-container">
          <p className="loading-message">문제를 생성하는 중입니다...</p>
        </div>
      </main>
    )
  }

  // Error state
  if (loadingError) {
    return (
      <main className="test-page">
        <div className="test-container">
          <p className="error-message">{loadingError}</p>
          <button
            type="button"
            className="back-button"
            onClick={() => navigate('/profile-review')}
          >
            <ArrowLeftIcon className="button-icon" />
            프로필 리뷰로 돌아가기
          </button>
        </div>
      </main>
    )
  }

  // No questions state
  if (questions.length === 0) {
    return (
      <main className="test-page">
        <div className="test-container">
          <p className="error-message">생성된 문제가 없습니다.</p>
        </div>
      </main>
    )
  }

  return (
    <main className="test-page">
      <div className="test-container">
        {/* Header with Timer and Save Status */}
        <div className="test-header">
          <Timer timeRemaining={timeRemaining} />
          <SaveStatus status={saveStatus} />
        </div>

        {/* Question */}
        <Question
          question={currentQuestion}
          currentIndex={currentIndex}
          totalQuestions={questions.length}
          answer={answer}
          onAnswerChange={setAnswer}
          disabled={isSubmitting}
        />

        {/* Submit Error */}
        {submitError && <p className="error-message">{submitError}</p>}

        {/* Next Button */}
        <button
          type="button"
          className="next-button"
          onClick={handleNextClick}
          disabled={!answer.trim() || isSubmitting}
        >
          {isSubmitting ? (
            '제출 중...'
          ) : currentIndex < questions.length - 1 ? (
            <>
              다음
              <ArrowRightIcon className="button-icon" />
            </>
          ) : (
            <>
              완료
              <CheckIcon className="button-icon" />
            </>
          )}
        </button>
      </div>
    </main>
  )
}

export default TestPage
