// REQ: REQ-F-B2-1, REQ-F-B2-2, REQ-F-B2-6
import React, { useEffect, useState, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { questionService } from '../services'
import { Timer, SaveStatus, Question, type QuestionData } from '../components/test'
import { useAutosave } from '../hooks/useAutosave'
import './TestPage.css'

/**
 * Test Page Component
 *
 * REQ: REQ-F-B2-1 - 생성된 문항을 순차적으로 표시
 * REQ: REQ-F-B2-2 - 진행률, 응답 입력, "다음" 버튼, 타이머 제공
 * REQ: REQ-F-B2-6 - 자동 저장 with visual feedback
 *
 * Features:
 * - Generate test questions on mount
 * - Display questions one by one
 * - Timer (20 minutes)
 * - Autosave answers
 * - Submit and navigate to results
 *
 * Route: /test
 */

type LocationState = {
  surveyId: string
  round: number
}

type GenerateQuestionsResponse = {
  session_id: string
  questions: QuestionData[]
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

  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as LocationState

  // Get current question
  const currentQuestion = questions[currentIndex] || null

  // Autosave hook
  const { saveStatus } = useAutosave({
    sessionId,
    currentQuestion,
    answer,
    questionStartTime,
  })

  // Load questions on mount
  useEffect(() => {
    const generateQuestions = async () => {
      if (!state?.surveyId) {
        setLoadingError('자기평가 정보가 없습니다. 프로필 리뷰 페이지로 돌아가주세요.')
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

        setSessionId(response.session_id)
        setQuestions(response.questions)
        setQuestionStartTime(Date.now())
        setIsLoading(false)
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : '문제 생성에 실패했습니다. 다시 시도해주세요.'
        setLoadingError(message)
        setIsLoading(false)
      }
    }

    generateQuestions()
  }, [state?.surveyId, state?.round])

  // Reset state when moving to next question
  useEffect(() => {
    setQuestionStartTime(Date.now())
    setSubmitError(null)
    setAnswer('')
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
      await questionService.autosave({
        session_id: sessionId,
        question_id: currentQuestion.id,
        user_answer: JSON.stringify(userAnswer),
      })

      // Move to next question or finish
      if (currentIndex < questions.length - 1) {
        setCurrentIndex(currentIndex + 1)
        setAnswer('')
        setIsSubmitting(false)
      } else {
        // All questions answered, navigate to results
        navigate('/test-results', { state: { sessionId } })
      }
    } catch (err) {
      const message =
        err instanceof Error ? err.message : '답변 제출에 실패했습니다.'
      setSubmitError(message)
      setIsSubmitting(false)
    }
  }, [sessionId, answer, isSubmitting, currentIndex, questions, navigate])

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
          {isSubmitting
            ? '제출 중...'
            : currentIndex < questions.length - 1
            ? '다음'
            : '완료'}
        </button>
      </div>
    </main>
  )
}

export default TestPage
