// REQ: REQ-F-B3-1, REQ-F-B3-2
import React, { useState, useEffect } from 'react'
import { useNavigate, useParams, useLocation } from 'react-router-dom'
import { ArrowLeftIcon, ArrowRightIcon, HomeIcon } from '@heroicons/react/24/outline'
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
        // TODO: Replace with actual API call
        // For now, using mock data
        const mockExplanations: QuestionExplanation[] = [
          {
            question_id: 'q1',
            question_number: 1,
            question_text: 'LLM의 핵심 아키텍처는 무엇인가?',
            user_answer: 'RNN',
            correct_answer: 'Transformer',
            is_correct: false,
            explanation_text:
              '[틀린 이유]\n사용자가 선택한 RNN은 과거의 시퀀스 모델링 방식입니다. 현대 LLM은 Transformer 아키텍처를 사용합니다.\n\n[정답의 원리]\nTransformer는 자기주의(Self-Attention) 메커니즘을 통해 입력 시퀀스의 모든 위치를 동시에 처리할 수 있어 병렬화가 가능하고 장거리 의존성을 효과적으로 학습합니다.\n\n[개념 구분]\nRNN은 순차적 처리로 느리고 장거리 의존성에 약한 반면, Transformer는 병렬 처리가 가능하고 위치 정보를 인코딩하여 모든 토큰 간 관계를 학습합니다.\n\n[복습 팁]\nTransformer 아키텍처의 핵심 요소(Self-Attention, Multi-Head Attention, Positional Encoding)를 정리하고, BERT와 GPT의 차이점을 학습하세요.',
            explanation_sections: [
              {
                title: '[틀린 이유]',
                content:
                  '사용자가 선택한 RNN은 과거의 시퀀스 모델링 방식입니다. 현대 LLM은 Transformer 아키텍처를 사용합니다.',
              },
              {
                title: '[정답의 원리]',
                content:
                  'Transformer는 자기주의(Self-Attention) 메커니즘을 통해 입력 시퀀스의 모든 위치를 동시에 처리할 수 있어 병렬화가 가능하고 장거리 의존성을 효과적으로 학습합니다.',
              },
              {
                title: '[개념 구분]',
                content:
                  'RNN은 순차적 처리로 느리고 장거리 의존성에 약한 반면, Transformer는 병렬 처리가 가능하고 위치 정보를 인코딩하여 모든 토큰 간 관계를 학습합니다.',
              },
              {
                title: '[복습 팁]',
                content:
                  'Transformer 아키텍처의 핵심 요소(Self-Attention, Multi-Head Attention, Positional Encoding)를 정리하고, BERT와 GPT의 차이점을 학습하세요.',
              },
            ],
            reference_links: [
              {
                title: 'Attention is All You Need (원논문)',
                url: 'https://arxiv.org/abs/1706.03762',
              },
              {
                title: 'Transformer 아키텍처 상세 해설',
                url: 'https://example.com/transformer-guide',
              },
              {
                title: 'LLM 학습 프로세스 완벽 이해',
                url: 'https://example.com/llm-training',
              },
            ],
          },
          {
            question_id: 'q2',
            question_number: 2,
            question_text: 'RAG의 주요 목적은 무엇인가?',
            user_answer: '검색된 정보를 LLM 입력으로 활용',
            correct_answer: '검색된 정보를 LLM 입력으로 활용',
            is_correct: true,
            explanation_text:
              '[정답입니다]\n정확합니다! RAG(Retrieval-Augmented Generation)의 핵심은 외부 지식을 검색하여 LLM의 생성 능력과 결합하는 것입니다.\n\n[핵심 개념]\nRAG는 벡터 데이터베이스에서 관련 문서를 검색한 후, 이를 컨텍스트로 LLM에 제공하여 더 정확하고 사실 기반의 답변을 생성합니다.\n\n[실무 활용]\n기업 내부 문서 검색, 고객 지원 챗봇, 의료 진단 보조 등에서 활용되며, LLM의 할루시네이션 문제를 크게 줄일 수 있습니다.',
            explanation_sections: [
              {
                title: '[정답입니다]',
                content:
                  '정확합니다! RAG(Retrieval-Augmented Generation)의 핵심은 외부 지식을 검색하여 LLM의 생성 능력과 결합하는 것입니다.',
              },
              {
                title: '[핵심 개념]',
                content:
                  'RAG는 벡터 데이터베이스에서 관련 문서를 검색한 후, 이를 컨텍스트로 LLM에 제공하여 더 정확하고 사실 기반의 답변을 생성합니다.',
              },
              {
                title: '[실무 활용]',
                content:
                  '기업 내부 문서 검색, 고객 지원 챗봇, 의료 진단 보조 등에서 활용되며, LLM의 할루시네이션 문제를 크게 줄일 수 있습니다.',
              },
            ],
            reference_links: [
              {
                title: 'RAG 시스템 구축 가이드',
                url: 'https://example.com/rag-implementation',
              },
              {
                title: '벡터 데이터베이스와 임베딩',
                url: 'https://example.com/vector-db',
              },
              {
                title: 'RAG 성능 최적화 전략',
                url: 'https://example.com/rag-optimization',
              },
            ],
          },
          {
            question_id: 'q3',
            question_number: 3,
            question_text: 'Prompt Engineering의 핵심 원칙은?',
            user_answer: '명확하고 구체적인 지시',
            correct_answer: '명확하고 구체적인 지시',
            is_correct: true,
            explanation_text:
              '[정답입니다]\n완벽합니다! Prompt Engineering의 가장 중요한 원칙은 LLM에게 명확하고 구체적인 지시를 제공하는 것입니다.\n\n[핵심 원리]\n좋은 프롬프트는 역할(Role), 맥락(Context), 작업(Task), 형식(Format)을 명확히 정의합니다. 예: "당신은 Python 전문가입니다. 초보자를 위한 Flask 튜토리얼을 3단계로 작성하세요."\n\n[실전 팁]\nFew-shot learning(예시 제공), Chain-of-Thought(단계별 사고), 제약 조건 명시 등의 기법을 활용하면 출력 품질이 크게 향상됩니다.',
            explanation_sections: [
              {
                title: '[정답입니다]',
                content:
                  '완벽합니다! Prompt Engineering의 가장 중요한 원칙은 LLM에게 명확하고 구체적인 지시를 제공하는 것입니다.',
              },
              {
                title: '[핵심 원리]',
                content:
                  '좋은 프롬프트는 역할(Role), 맥락(Context), 작업(Task), 형식(Format)을 명확히 정의합니다. 예: "당신은 Python 전문가입니다. 초보자를 위한 Flask 튜토리얼을 3단계로 작성하세요."',
              },
              {
                title: '[실전 팁]',
                content:
                  'Few-shot learning(예시 제공), Chain-of-Thought(단계별 사고), 제약 조건 명시 등의 기법을 활용하면 출력 품질이 크게 향상됩니다.',
              },
            ],
            reference_links: [
              {
                title: 'OpenAI Prompt Engineering Guide',
                url: 'https://platform.openai.com/docs/guides/prompt-engineering',
              },
              {
                title: 'Chain-of-Thought Prompting 논문',
                url: 'https://arxiv.org/abs/2201.11903',
              },
              {
                title: 'Prompt Engineering Best Practices',
                url: 'https://example.com/prompt-best-practices',
              },
            ],
          },
        ]

        // Simulate API delay
        await new Promise((resolve) => setTimeout(resolve, 500))

        setExplanations(mockExplanations)
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
            <span className="answer-value">{currentExplanation.user_answer}</span>
            <span className={`answer-badge ${currentExplanation.is_correct ? 'correct' : 'incorrect'}`}>
              {currentExplanation.is_correct ? '정답' : '오답'}
            </span>
          </div>
          {!currentExplanation.is_correct && (
            <div className="answer-row correct">
              <span className="answer-label">정답:</span>
              <span className="answer-value">{currentExplanation.correct_answer}</span>
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
