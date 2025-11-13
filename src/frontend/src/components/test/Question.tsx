// Question component for displaying test questions
// REQ: REQ-F-B2-1

import React from 'react'
import './Question.css'

export interface QuestionData {
  id: string
  item_type: string
  stem: string
  choices: string[] | null
  difficulty: number
  category: string
}

interface QuestionProps {
  question: QuestionData
  currentIndex: number
  totalQuestions: number
  answer: string
  onAnswerChange: (answer: string) => void
  disabled?: boolean
}

/**
 * Question Component
 *
 * Displays a test question with appropriate input based on question type
 */
export const Question: React.FC<QuestionProps> = ({
  question,
  currentIndex,
  totalQuestions,
  answer,
  onAnswerChange,
  disabled = false,
}) => {
  const renderAnswerInput = () => {
    if (question.item_type === 'multiple_choice') {
      return (
        <div className="choices-container">
          {question.choices?.map((choice, index) => (
            <label key={index} className="choice-label">
              <input
                type="radio"
                name={`question-${question.id}`}
                value={choice}
                checked={answer === choice}
                onChange={(e) => onAnswerChange(e.target.value)}
                disabled={disabled}
                className="choice-input"
              />
              <span className="choice-text">{choice}</span>
            </label>
          ))}
        </div>
      )
    }

    if (question.item_type === 'true_false') {
      return (
        <div className="choices-container">
          <label className="choice-label">
            <input
              type="radio"
              name={`question-${question.id}`}
              value="true"
              checked={answer === 'true'}
              onChange={(e) => onAnswerChange(e.target.value)}
              disabled={disabled}
              className="choice-input"
            />
            <span className="choice-text">True</span>
          </label>
          <label className="choice-label">
            <input
              type="radio"
              name={`question-${question.id}`}
              value="false"
              checked={answer === 'false'}
              onChange={(e) => onAnswerChange(e.target.value)}
              disabled={disabled}
              className="choice-input"
            />
            <span className="choice-text">False</span>
          </label>
        </div>
      )
    }

    // short_answer
    return (
      <textarea
        className="answer-textarea"
        value={answer}
        onChange={(e) => onAnswerChange(e.target.value)}
        placeholder="답변을 입력하세요..."
        rows={5}
        disabled={disabled}
      />
    )
  }

  return (
    <div className="question-container">
      {/* Progress */}
      <div className="question-progress">
        문제 {currentIndex + 1} / {totalQuestions}
      </div>

      {/* Category & Difficulty */}
      <div className="question-meta">
        <span className="question-category">{question.category}</span>
        <span className="question-difficulty">난이도 {question.difficulty}</span>
      </div>

      {/* Question text */}
      <div className="question-stem">{question.stem}</div>

      {/* Answer input */}
      {renderAnswerInput()}
    </div>
  )
}
