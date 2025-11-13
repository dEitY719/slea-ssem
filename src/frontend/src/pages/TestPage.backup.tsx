// REQ: REQ-F-B2-1, REQ-F-B2-2, REQ-F-B2-6
import React, { useEffect, useState, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { questionService } from '../services'
import './TestPage.css'

/**
 * Test Page Component
 *
 * REQ: REQ-F-B2-1 - 생성된 문항을 순차적으로 표시
 * REQ: REQ-F-B2-2 - 진행률, 응답 입력, "다음" 버튼, 타이머 제공
 *
 * Features:
 * - Generate test questions on mount
 * - Display questions one by one
 * - Show progress (e.g., 1/5)
 * - Timer (20 minutes)
 * - Submit answer and move to next question
 *
 * Route: /test
 */

type LocationState = {
  surveyId: string
  round: number
}

type Question = {
  id: string
  item_type: string
  stem: string
  choices: string[] | null
  difficulty: number
  category: string
}

type GenerateQuestionsResponse = {
  session_id: string
  questions: Question[]
}

/**
 * Helper: Get timer color based on remaining time (REQ-F-B2-5)
 * @param seconds - Remaining time in seconds
 * @returns Color string ('green' | 'orange' | 'red')
 */
const getTimerColor = (seconds: number): string => {
  if (seconds > 15 * 60) return 'green'   // 16+ minutes
  if (seconds > 5 * 60) return 'orange'   // 6-15 minutes
  return 'red'                             // 5 minutes or less
}

/**
 * Helper: Format time as MM:SS (REQ-F-B2-2)
 * @param seconds - Time in seconds
 * @returns Formatted time string (e.g., "20:00")
 */
const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const TestPage: React.FC = () => {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [questions, setQuestions] = useState<Question[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answer, setAnswer] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [loadingError, setLoadingError] = useState<string | null>(null)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [questionStartTime, setQuestionStartTime] = useState<number>(Date.now())
  const [timeRemaining, setTimeRemaining] = useState<number>(1200) // 20 minutes = 1200 seconds
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
  const [lastSavedAnswer, setLastSavedAnswer] = useState<string>('')
  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as LocationState

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
        setQuestionStartTime(Date.now()) // Reset timer when questions loaded
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

  // Reset timer and clear submit error when moving to next question
  useEffect(() => {
    setQuestionStartTime(Date.now())
    setSubmitError(null)
    setLastSavedAnswer('')
    setSaveStatus('idle')
    setAnswer('') // Clear answer when moving to next question
  }, [currentIndex])

  // Timer countdown logic (REQ-F-B2-2, REQ-F-B2-5)
  useEffect(() => {
    // Only start timer when sessionId and questions are ready
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

  // Autosave logic (REQ-F-B2-6)
  useEffect(() => {
    // Only autosave if answer is not empty, different from last saved, and session is ready
    if (!answer.trim() || answer === lastSavedAnswer || !sessionId || !questions || questions.length === 0) {
      return
    }

    const timer = setTimeout(async () => {
      setSaveStatus('saving')
      try {
        const currentQuestion = questions[currentIndex]
        const responseTimeMs = Date.now() - questionStartTime

        let userAnswer: { selected?: string; text?: string }
        if (currentQuestion.item_type === 'multiple_choice' || currentQuestion.item_type === 'true_false') {
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
    }, 1000) // 1 second debounce

    return () => clearTimeout(timer)
  }, [answer, sessionId, questions, currentIndex, questionStartTime, lastSavedAnswer])

  const handleNextClick = useCallback(async () => {
    if (!sessionId || !answer.trim() || isSubmitting) {
      return
    }

    setIsSubmitting(true)
    setSubmitError(null) // Clear previous submit errors

    try {
      const currentQuestion = questions[currentIndex]
      const responseTimeMs = Date.now() - questionStartTime

      // Build user_answer based on question type
      let userAnswer: { selected?: string; text?: string }
      if (currentQuestion.item_type === 'multiple_choice' || currentQuestion.item_type === 'true_false') {
        userAnswer = { selected: answer }
      } else {
        // short_answer
        userAnswer = { text: answer }
      }

      // Submit answer to backend
      await questionService.autosave({
        session_id: sessionId,
        question_id: currentQuestion.id,
        user_answer: JSON.stringify(userAnswer),
      })

      // Move to next question
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
  }, [sessionId, answer, isSubmitting, currentIndex, questions, navigate, questionStartTime])

  if (isLoading) {
    return (
      <main className="test-page">
        <div className="test-container">
          <p className="loading-message">문제를 생성하는 중입니다...</p>
        </div>
      </main>
    )
  }

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

  if (questions.length === 0) {
    return (
      <main className="test-page">
        <div className="test-container">
          <p className="error-message">생성된 문제가 없습니다.</p>
        </div>
      </main>
    )
  }

  const currentQuestion = questions[currentIndex]
  const progress = `${currentIndex + 1}/${questions.length}`

  return (
    <main className="test-page">
      <div className="test-container">
        <div className="test-header">
          <h1 className="page-title">AI 역량 레벨 테스트</h1>
          <div className="header-info">
            <p className="progress">진행률: {progress}</p>
            <div className={`timer timer-${getTimerColor(timeRemaining)}`}>
              남은 시간: {formatTime(timeRemaining)}
            </div>
          </div>
        </div>

        <div className="question-section">
          <h2 className="question-number">문제 {currentIndex + 1}</h2>
          <p className="question-text">{currentQuestion.stem}</p>

          {currentQuestion.item_type === 'multiple_choice' && currentQuestion.choices && (
            <div className="choices">
              {currentQuestion.choices.map((choice, index) => (
                <label key={index} className="choice-item">
                  <input
                    type="radio"
                    name="answer"
                    value={choice}
                    checked={answer === choice}
                    onChange={(e) => setAnswer(e.target.value)}
                  />
                  <span className="choice-text">{choice}</span>
                </label>
              ))}
            </div>
          )}

          {currentQuestion.item_type === 'true_false' && (
            <div className="choices">
              <label className="choice-item">
                <input
                  type="radio"
                  name="answer"
                  value="true"
                  checked={answer === 'true'}
                  onChange={(e) => setAnswer(e.target.value)}
                />
                <span className="choice-text">참 (True)</span>
              </label>
              <label className="choice-item">
                <input
                  type="radio"
                  name="answer"
                  value="false"
                  checked={answer === 'false'}
                  onChange={(e) => setAnswer(e.target.value)}
                />
                <span className="choice-text">거짓 (False)</span>
              </label>
            </div>
          )}

          {currentQuestion.item_type === 'short_answer' && (
            <textarea
              className="answer-input"
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="답변을 입력하세요"
              rows={5}
            />
          )}
        </div>

        <div className="button-group">
          <button
            type="button"
            className="next-button"
            onClick={handleNextClick}
            disabled={!answer.trim() || isSubmitting}
          >
            {currentIndex < questions.length - 1
              ? '다음 문제'
              : '테스트 완료'}
          </button>
        </div>

        <div className="info-box">
          <p className="info-text">
            답변을 선택하거나 입력한 후 "{currentIndex < questions.length - 1 ? '다음 문제' : '테스트 완료'}" 버튼을 클릭하세요.
          </p>
        </div>

        {submitError && (
          <div className="error-box">
            <p className="error-message">{submitError}</p>
          </div>
        )}
      </div>

      {/* Autosave status indicator - REQ-F-B2-6 */}
      {saveStatus === 'saving' && (
        <div className="save-status save-status-saving">
          저장 중...
        </div>
      )}

      {saveStatus === 'saved' && (
        <div className="save-status save-status-saved">
          ✓ 저장됨
        </div>
      )}

      {saveStatus === 'error' && (
        <div className="save-status save-status-error">
          저장 실패
        </div>
      )}
    </main>
  )
}

export default TestPage
