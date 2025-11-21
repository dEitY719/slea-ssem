// REQ: REQ-F-B3-1, REQ-F-B3-2
import React, { useState, useEffect } from 'react'
import { useNavigate, useParams, useLocation } from 'react-router-dom'
import { ArrowLeftIcon, ArrowRightIcon, HomeIcon } from '@heroicons/react/24/outline'
import { transport } from '../lib/transport'
import './ExplanationPage.css'

/**
 * Explanation Page Component
 *
 * REQ: REQ-F-B3 - 해설 화면
 *
 * Features:
 * - REQ-F-B3-1: Display question explanations with reference links
 * - REQ-F-B3-2: Provide "Next Question" and "View Results" navigation
 *
 * Route: /test-explanations/:sessionId
 */

interface ExplanationSection {
  title: string
  content: string
}

interface ReferenceLink {
  title: string
  url: string
}

interface QuestionExplanation {
  question_id: string
  question_number: number
  question_text: string
  user_answer: string
  correct_answer: string
  is_correct: boolean
  explanation_text: string
  explanation_sections: ExplanationSection[]
  reference_links: ReferenceLink[]
}

type LocationState = {
  questionIndex?: number
}

const ExplanationPage: React.FC = () => {
  const navigate = useNavigate()
  const { sessionId } = useParams<{ sessionId: string }>()
  const location = useLocation()
  const state = location.state as LocationState | null

  const [currentIndex, setCurrentIndex] = useState(state?.questionIndex || 0)
  const [explanations, setExplanations] = useState<QuestionExplanation[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Helper function to convert answer to string
  const formatAnswer = (answer: any): string => {
    if (typeof answer === 'string') return answer
    if (typeof answer === 'object' && answer !== null) {
      return answer.selected_key || answer.answer || answer.text || JSON.stringify(answer)
    }
    return String(answer)
  }

  // Fetch explanations on mount
  useEffect(() => {
    const fetchExplanations = async () => {
      if (!sessionId) {
        setError('세션 ID가 없습니다.')
        setIsLoading(false)
        return
      }

      setIsLoading(true)
      setError(null)

      try {
        // Fetch explanations from backend API using transport layer
        const data = await transport.get<{ explanations: QuestionExplanation[] }>(
          `/api/questions/explanations/session/${sessionId}`
        )
        const fetchedExplanations: QuestionExplanation[] = data.explanations || []

        setExplanations(fetchedExplanations)
        setIsLoading(false)
      } catch (err) {
        setError('해설을 불러오는 중 오류가 발생했습니다.')
        setIsLoading(false)
      }
    }

    fetchExplanations()
  }, [sessionId])

  // Handle navigation
  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1)
    }
  }

  const handleNext = () => {
    if (currentIndex < explanations.length - 1) {
      setCurrentIndex(currentIndex + 1)
    }
  }

  const handleViewResults = () => {
    navigate('/test-results', { state: { sessionId } })
  }

  // Loading state
  if (isLoading) {
    return (
      <main className="explanation-page">
        <div className="explanation-container">
          <p className="loading-text">해설을 불러오는 중입니다...</p>
        </div>
      </main>
    )
  }

  // Error state
  if (error) {
    return (
      <main className="explanation-page">
        <div className="explanation-container">
          <p className="error-message">{error}</p>
          <button type="button" className="back-button" onClick={() => navigate('/home')}>
            <HomeIcon className="button-icon" />
            홈으로 돌아가기
          </button>
        </div>
      </main>
    )
  }

  // No data
  if (explanations.length === 0) {
    return (
      <main className="explanation-page">
        <div className="explanation-container">
          <p className="error-message">해설 데이터가 없습니다.</p>
        </div>
      </main>
    )
  }

  const currentExplanation = explanations[currentIndex]
  const isFirstQuestion = currentIndex === 0
  const isLastQuestion = currentIndex === explanations.length - 1

  return (
    <main className="explanation-page">
      <div className="explanation-container">
        {/* Header */}
        <div className="explanation-header">
          <h1 className="explanation-title">문항별 해설</h1>
          <div className="progress-indicator">
            <span className="progress-text">
              {currentIndex + 1} / {explanations.length}
            </span>
          </div>
        </div>

        {/* Question Info */}
        <div className="question-info">
          <h2 className="question-title">문제 {currentExplanation.question_number}</h2>
          <p className="question-text">{currentExplanation.question_text}</p>
        </div>

        {/* Answer Comparison */}
        <div className="answer-comparison">
          <div className={`answer-row ${currentExplanation.is_correct ? 'correct' : 'incorrect'}`}>
            <span className="answer-label">내 답변:</span>
            <span className="answer-value">{formatAnswer(currentExplanation.user_answer)}</span>
            <span className={`answer-badge ${currentExplanation.is_correct ? 'correct' : 'incorrect'}`}>
              {currentExplanation.is_correct ? '정답' : '오답'}
            </span>
          </div>
          {!currentExplanation.is_correct && (
            <div className="answer-row correct">
              <span className="answer-label">정답:</span>
              <span className="answer-value">{formatAnswer(currentExplanation.correct_answer)}</span>
            </div>
          )}
        </div>

        {/* Explanation Sections */}
        <div className="explanation-content">
          <h3 className="section-title">해설</h3>
          {currentExplanation.explanation_sections.map((section, index) => (
            <div key={index} className="explanation-section">
              <h4 className="section-heading">{section.title}</h4>
              <p className="section-text">{section.content}</p>
            </div>
          ))}
        </div>

        {/* Reference Links - REQ: REQ-F-B3-1 */}
        <div className="reference-links">
          <h3 className="section-title">참고 자료</h3>
          <ul className="links-list">
            {currentExplanation.reference_links.map((link, index) => (
              <li key={index} className="link-item">
                <a
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="reference-link"
                >
                  {link.title}
                </a>
              </li>
            ))}
          </ul>
        </div>

        {/* Navigation Buttons - REQ: REQ-F-B3-2 */}
        <div className="navigation-buttons">
          {!isFirstQuestion && (
            <button type="button" className="nav-button prev-button" onClick={handlePrevious}>
              <ArrowLeftIcon className="button-icon" />
              이전 문항
            </button>
          )}

          {!isLastQuestion && (
            <button type="button" className="nav-button next-button" onClick={handleNext}>
              다음 문항
              <ArrowRightIcon className="button-icon" />
            </button>
          )}

          {isLastQuestion && (
            <button type="button" className="nav-button results-button" onClick={handleViewResults}>
              <HomeIcon className="button-icon" />
              결과 보기
            </button>
          )}
        </div>
      </div>
    </main>
  )
}

export default ExplanationPage
