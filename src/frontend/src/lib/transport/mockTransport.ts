// Mock HTTP transport for development without backend

import { HttpTransport, RequestConfig } from './types'
import { debugLog } from '../../utils/logger'

const API_AUTH_LOGIN = '/api/auth/login'
const API_AUTH_STATUS = '/api/auth/status'
const API_PROFILE_NICKNAME = '/api/profile/nickname'
const API_PROFILE_NICKNAME_CHECK = '/api/profile/nickname/check'
const API_PROFILE_REGISTER = '/api/profile/register'
const API_PROFILE_CONSENT = '/api/profile/consent'
const API_PROFILE_SURVEY = '/api/profile/survey'
const API_PROFILE_HISTORY = '/api/profile/history'
const API_QUESTIONS_GENERATE = '/api/questions/generate'
const API_QUESTIONS_GENERATE_ADAPTIVE = '/api/questions/generate-adaptive'
const API_QUESTIONS_AUTOSAVE = '/api/questions/autosave'
const API_QUESTIONS_SCORE = '/api/questions/score'
const API_SESSION_COMPLETE = '/api/questions/session'
const API_QUESTIONS_EXPLANATIONS = '/api/questions/explanations/session'
const API_PROFILE_RANKING = '/api/profile/ranking'
const API_RESULTS_PREVIOUS = '/api/results/previous'
const API_PROFILE_LAST_TEST_RESULT = '/api/profile/last-test-result'
const API_STATISTICS_TOTAL_PARTICIPANTS = '/api/statistics/total-participants'

const ensureApiPath = (url: string): string => {
  if (url.startsWith('http://') || url.startsWith('https://')) {
    try {
      const parsed = new URL(url)
      return ensureApiPath(parsed.pathname)
    } catch {
      return url
    }
  }

  if (url === '/api' || url.startsWith('/api/')) {
    return url
  }

  const sanitized = url.startsWith('/') ? url : `/${url}`
  return `/api${sanitized}`
}

// Mock data storage: 엔드포인트별로 미리 정의된 가짜 데이터 저장
const mockData: Record<string, any> = {
  [API_AUTH_LOGIN]: {
    access_token: 'mock_access_token',
    token_type: 'bearer',
    user_id: 'mock_user@samsung.com',
    is_new_user: true,
  },
  [API_AUTH_STATUS]: {
    authenticated: true,
    user_id: 'mock_user@samsung.com',
  },
  [API_PROFILE_NICKNAME]: {
    user_id: 'mock_user@samsung.com',
    nickname: null,  // Change to 'mockuser' to test nickname exists
    registered_at: null,
    updated_at: null,
  },
  [API_PROFILE_NICKNAME_CHECK]: {
    available: true,
    suggestions: [],
  },
  [API_PROFILE_CONSENT]: {
    consented: false,  // Change to true to test already consented user
    consent_at: null,
  },
  [API_PROFILE_SURVEY]: {
    level: null,
    career: null,
    job_role: null,
    duty: null,
    interests: null,
  },
  [API_PROFILE_HISTORY]: {
    nickname: 'mockuser',
    survey: {
      survey_id: 'survey_previous_123',
      level: 'intermediate',
      career: 5,
      job_role: 'SW',
      duty: 'Backend Development',
      interests: ['AI', 'Backend'],
    },
    last_test_date: '2025-11-15T10:30:00Z',
  },
  [API_QUESTIONS_GENERATE]: {
    session_id: 'mock_session_123',
    questions: [
      {
        id: 'q1',
        item_type: 'multiple_choice',
        stem: 'What is the primary goal of machine learning?',
        choices: [
          'To replace human intelligence',
          'To enable computers to learn from data',
          'To create artificial consciousness',
          'To build faster processors'
        ],
        difficulty: 3,
        category: 'AI Basics',
      },
      {
        id: 'q2',
        item_type: 'true_false',
        stem: 'Deep learning is a subset of machine learning.',
        choices: null,
        difficulty: 2,
        category: 'AI Basics',
      },
      {
        id: 'q3',
        item_type: 'short_answer',
        stem: 'Explain the difference between supervised and unsupervised learning.',
        choices: null,
        difficulty: 5,
        category: 'ML Fundamentals',
      },
      {
        id: 'q4',
        item_type: 'multiple_choice',
        stem: 'Which algorithm is commonly used for classification tasks?',
        choices: [
          'K-means clustering',
          'Random Forest',
          'PCA',
          'DBSCAN'
        ],
        difficulty: 4,
        category: 'ML Algorithms',
      },
      {
        id: 'q5',
        item_type: 'short_answer',
        stem: 'What is overfitting and how can you prevent it?',
        choices: null,
        difficulty: 6,
        category: 'ML Fundamentals',
        },
      ],
    },
    [API_QUESTIONS_AUTOSAVE]: {
      success: true,
      message: 'Answer autosaved successfully',
      autosave_id: 'autosave_mock_123',
      saved_at: new Date().toISOString(),
    },
  // REQ: REQ-F-A1-Home - Last test result
  [API_PROFILE_LAST_TEST_RESULT]: {
    hasResult: true,
    grade: 3,
    completedAt: '2025-01-15',
    badgeUrl: null,
  },
  // REQ: REQ-F-A1-Home - Total participants
  [API_STATISTICS_TOTAL_PARTICIPANTS]: {
    totalParticipants: 1234,
  },
  // Add more mock endpoints here
}

type GradeResultMock = {
  user_id: number
  grade: string
  score: number
  rank: number
  total_cohort_size: number
  percentile: number
  percentile_confidence: 'medium' | 'high'
  percentile_description: string
  grade_distribution: Array<{
    grade: string
    count: number
    percentage: number
  }>
}

type PreviousResultSummary = {
  grade: string
  score: number
  test_date: string
}

const RESULT_SEQUENCE: GradeResultMock[] = [
  {
    user_id: 1,
    grade: 'Beginner',
    score: 58,
    rank: 420,
    total_cohort_size: 506,
    percentile: 24,
    percentile_confidence: 'medium',
    percentile_description: '상위 76%',
    grade_distribution: [
      { grade: 'Beginner', count: 198, percentage: 39.1 },
      { grade: 'Intermediate', count: 152, percentage: 30.0 },
      { grade: 'Inter-Advanced', count: 76, percentage: 15.0 },
      { grade: 'Advanced', count: 52, percentage: 10.3 },
      { grade: 'Elite', count: 28, percentage: 5.6 },
    ],
  },
  {
    user_id: 1,
    grade: 'Advanced',
    score: 88,
    rank: 48,
    total_cohort_size: 506,
    percentile: 91,
    percentile_confidence: 'high',
    percentile_description: '상위 9%',
    grade_distribution: [
      { grade: 'Beginner', count: 80, percentage: 15.8 },
      { grade: 'Intermediate', count: 146, percentage: 28.8 },
      { grade: 'Inter-Advanced', count: 138, percentage: 27.3 },
      { grade: 'Advanced', count: 94, percentage: 18.6 },
      { grade: 'Elite', count: 48, percentage: 9.5 },
    ],
  },
]

const TEST_DATE_SEQUENCE = [
  '2025-01-10T10:00:00Z',
  '2025-02-18T09:45:00Z',
  '2025-03-22T09:30:00Z',
]

let sessionSequenceCounter = 0
const sessionAttemptOrder = new Map<string, number>()
const sessionResultsCache = new Map<string, GradeResultMock>()
const completedResultsHistory: PreviousResultSummary[] = []
let nextPreviousResult: PreviousResultSummary | null = null

// Track recent generate requests to prevent StrictMode double-calls
const recentGenerateRequests = new Map<string, { sessionId: string; timestamp: number }>()

const hasMockOverride = (endpoint: string): boolean =>
  Object.prototype.hasOwnProperty.call(mockData, endpoint)

const isEndpointOverridden = (endpoint: string): boolean =>
  overriddenEndpoints.has(endpoint)

const deepClone = <T>(data: T): T => JSON.parse(JSON.stringify(data))

const cloneQuestions = (questions: any[]) =>
  questions.map(question => ({
    ...question,
    choices: Array.isArray(question.choices) ? [...question.choices] : null,
  }))

const determineTestDate = (attemptIndex: number): string => {
  const templateIndex = Math.min(attemptIndex - 1, TEST_DATE_SEQUENCE.length - 1)
  return TEST_DATE_SEQUENCE[templateIndex] ?? new Date().toISOString()
}

const preparePreviousResultForAttempt = (attemptIndex: number) => {
  const previousAttemptIndex = attemptIndex - 1
  if (previousAttemptIndex <= 0) {
    nextPreviousResult = null
    return
  }

  const fallback = completedResultsHistory[completedResultsHistory.length - 1] ?? null
  nextPreviousResult = completedResultsHistory[previousAttemptIndex - 1] ?? fallback
}

const buildSessionId = (attemptIndex: number) =>
  `mock_session_${String(attemptIndex).padStart(3, '0')}`

const beginAttempt = (): number => {
  sessionSequenceCounter += 1
  preparePreviousResultForAttempt(sessionSequenceCounter)
  return sessionSequenceCounter
}

const registerSessionAttempt = (sessionId: string, attemptIndex: number) => {
  sessionAttemptOrder.set(sessionId, attemptIndex)
}

const resolveAttemptIndex = (sessionId: string): number => {
  const existing = sessionAttemptOrder.get(sessionId)
  if (existing) {
    return existing
  }
  const fallback = sessionSequenceCounter || 1
  sessionAttemptOrder.set(sessionId, fallback)
  return fallback
}

const recordCompletedResult = (attemptIndex: number, result: GradeResultMock) => {
  const summary: PreviousResultSummary = {
    grade: result.grade,
    score: Math.round(result.score),
    test_date: determineTestDate(attemptIndex),
  }
  completedResultsHistory[attemptIndex - 1] = summary
}

const getResultForAttempt = (attemptIndex: number): GradeResultMock => {
  const templateIndex = Math.min(attemptIndex - 1, RESULT_SEQUENCE.length - 1)
  return deepClone(RESULT_SEQUENCE[templateIndex])
}

const resetResultProgression = () => {
  sessionSequenceCounter = 0
  sessionAttemptOrder.clear()
  sessionResultsCache.clear()
  completedResultsHistory.length = 0
  nextPreviousResult = null
  recentGenerateRequests.clear()
}

const overriddenEndpoints = new Set<string>()

// Track taken nicknames for mock: 이미 사용 중인 닉네임 목록
const takenNicknames = new Set(['mockuser', 'existing_user'])

// REQ: REQ-F-A2-5 - Forbidden words list (금칙어)
const FORBIDDEN_WORDS = [
  'admin',
  'administrator',
  'system',
  'root',
  'moderator',
  'mod',
  'staff',
  'support',
  'bot',
  'service',
  'account',
  'user',
  'test',
  'temp',
  'guest',
  'anonymous',
]

// REQ: REQ-F-A2-3, REQ-F-A2-5 - Nickname validation helper
const validateNickname = (nickname: string): { valid: boolean; error?: string } => {
  // Validate length (3-30 characters)
  if (nickname.length < 3) {
    return { valid: false, error: '닉네임은 3자 이상이어야 합니다.' }
  }

  if (nickname.length > 30) {
    return { valid: false, error: '닉네임은 30자 이하여야 합니다.' }
  }

  // Validate format: alphanumeric + underscore only
  const validPattern = /^[a-zA-Z0-9_]+$/
  if (!validPattern.test(nickname)) {
    return { valid: false, error: '닉네임은 영문자, 숫자, 언더스코어만 사용 가능합니다.' }
  }

  // Check forbidden words (case-insensitive)
  const nicknameLower = nickname.toLowerCase()

  // Exact match check
  if (FORBIDDEN_WORDS.includes(nicknameLower)) {
    return {
      valid: false,
      error: `'${nickname}'은(는) 사용할 수 없는 닉네임입니다. 다른 닉네임을 선택해주세요.`,
    }
  }

  // Check if nickname starts with forbidden word
  for (const forbidden of FORBIDDEN_WORDS) {
    if (nicknameLower.startsWith(forbidden)) {
      return {
        valid: false,
        error: '닉네임에 사용할 수 없는 단어가 포함되어 있습니다. 다른 닉네임을 선택해주세요.',
      }
    }
  }

  return { valid: true }
}

type RequestLogEntry = {
  url: string
  method: string
  body?: any
}

const requestLog: RequestLogEntry[] = []
const endpointErrors = new Map<string, string>()

// Mock configuration: 네트워크 지연, 에러 여부 등 시뮬레이션 설정
export const mockConfig = {
  delay: 500,           // Network delay in ms
  simulateError: false, // Simulate API errors
  slowNetwork: false,   // Simulate slow network (3s delay)
}

// 실제로 요청을 처리하는 객체
class MockTransport implements HttpTransport {
  private async mockRequest<T>(url: string, method: string, requestData?: any): Promise<T> {
    const normalizedUrl = ensureApiPath(url)
    requestLog.push({ url: normalizedUrl, method, body: requestData })
    debugLog(`[Mock Transport] ${method} ${normalizedUrl}`, requestData)

    // Simulate network delay
    const delay = mockConfig.slowNetwork ? 3000 : mockConfig.delay
    await new Promise(resolve => setTimeout(resolve, delay))

    // Endpoint-specific error override
    const endpointError = endpointErrors.get(normalizedUrl)
    if (endpointError) {
      throw new Error(endpointError)
    }

    // Simulate error
    if (mockConfig.simulateError) {
      throw new Error('Mock Transport: Simulated API error')
    }

    // Handle auth login endpoint
      if (normalizedUrl === API_AUTH_LOGIN && method === 'POST') {
        const response = mockData[API_AUTH_LOGIN]
        if (!response) {
          throw new Error('Mock login response not configured')
        }
        debugLog('[Mock Transport] Response:', response)
        return response as T
      }

    // Handle nickname check endpoint
    if (normalizedUrl === API_PROFILE_NICKNAME_CHECK && method === 'POST' && requestData?.nickname) {
      const nickname = requestData.nickname

      // REQ: REQ-F-A2-3, REQ-F-A2-5 - Validate nickname format and forbidden words
      const validation = validateNickname(nickname)
      if (!validation.valid) {
        throw new Error(validation.error)
      }

      const isTaken = takenNicknames.has(nickname.toLowerCase())

      const response = {
        available: !isTaken,
        suggestions: isTaken ? [
          `${nickname}_1`,
          `${nickname}_2`,
          `${nickname}_3`
        ] : []
      }

      debugLog('[Mock Transport] Response:', response)
      return response as T
    }

      // Handle nickname register endpoint
    if (normalizedUrl === API_PROFILE_REGISTER && method === 'POST' && requestData?.nickname) {
      const nickname: string = requestData.nickname

      // REQ: REQ-F-A2-3, REQ-F-A2-5 - Validate nickname format and forbidden words
      const validation = validateNickname(nickname)
      if (!validation.valid) {
        throw new Error(validation.error)
      }

      if (takenNicknames.has(nickname.toLowerCase())) {
        throw new Error('이미 사용 중인 닉네임입니다.')
      }

      takenNicknames.add(nickname.toLowerCase())
      mockData[API_PROFILE_NICKNAME] = {
        ...mockData[API_PROFILE_NICKNAME],
        nickname,
        registered_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      const response = {
        success: true,
        message: '닉네임 등록 완료',
        user_id: 'mock_user@samsung.com',
        nickname,
        registered_at: mockData[API_PROFILE_NICKNAME].registered_at,
      }

      debugLog('[Mock Transport] Response:', response)
      return response as T
    }

    // Handle consent update endpoint
    if (normalizedUrl === API_PROFILE_CONSENT && method === 'POST') {
      const consent = requestData?.consent

      if (typeof consent !== 'boolean') {
        throw new Error('consent must be a boolean')
      }

      // Update mock consent data
      mockData[API_PROFILE_CONSENT] = {
        consented: consent,
        consent_at: consent ? new Date().toISOString() : null,
      }

      const response = {
        message: consent ? '개인정보 수집 및 이용에 동의하였습니다.' : '동의가 철회되었습니다.',
        consented: consent,
        consent_at: mockData[API_PROFILE_CONSENT].consent_at,
      }

      debugLog('[Mock Transport] Consent updated:', mockData[API_PROFILE_CONSENT])
      debugLog('[Mock Transport] Response:', response)
      return response as T
    }

    // Handle survey update endpoint
    if (normalizedUrl === API_PROFILE_SURVEY && method === 'PUT') {
      const validLevels = ['beginner', 'intermediate', 'inter-advanced', 'advanced', 'elite']

      // Validate level if provided
      if (requestData?.level && !validLevels.includes(requestData.level)) {
        throw new Error('Invalid level. Must be one of: beginner, intermediate, inter-advanced, advanced, elite')
      }

      // Validate career if provided
      if (requestData?.career !== undefined && requestData?.career !== null) {
        const career = requestData.career
        if (typeof career !== 'number' || career < 0 || career > 60) {
          throw new Error('career must be a number between 0 and 60')
        }
      }

      // Validate job_role if provided
      if (requestData?.job_role) {
        if (typeof requestData.job_role !== 'string' || requestData.job_role.length > 100) {
          throw new Error('job_role must be a string with max 100 characters')
        }
      }

      // Validate duty if provided
      if (requestData?.duty) {
        if (typeof requestData.duty !== 'string' || requestData.duty.length > 500) {
          throw new Error('duty must be a string with max 500 characters')
        }
      }

      // Validate interests if provided
      if (requestData?.interests) {
        if (!Array.isArray(requestData.interests) || requestData.interests.length > 20) {
          throw new Error('interests must be an array with max 20 items')
        }
      }

      // Update mock survey data
      mockData[API_PROFILE_SURVEY] = {
        ...mockData[API_PROFILE_SURVEY],
        ...requestData,
      }

      const response = {
        success: true,
        message: '자기평가 정보 업데이트 완료',
        user_id: 'mock_user@samsung.com',
        survey_id: `survey_${Date.now()}`,
        updated_at: new Date().toISOString(),
      }

      debugLog('[Mock Transport] Survey updated:', mockData[API_PROFILE_SURVEY])
      debugLog('[Mock Transport] Response:', response)
      return response as T
    }

    // Handle questions generate endpoint
    if (normalizedUrl === API_QUESTIONS_GENERATE && method === 'POST') {
      debugLog('[Mock Transport] Generating questions for:', requestData)
        const template = mockData[API_QUESTIONS_GENERATE]
        if (!template) {
          throw new Error('Mock questions response not configured')
        }

        // Check for recent duplicate request (StrictMode protection)
        const surveyId = requestData?.survey_id || 'default'
        const requestKey = `${surveyId}_${requestData?.round || 1}`
        const recentRequest = recentGenerateRequests.get(requestKey)
        const now = Date.now()

        // If same request within 2 seconds, return cached session
        if (recentRequest && now - recentRequest.timestamp < 2000) {
          debugLog('[Mock Transport] Returning cached session for duplicate request:', recentRequest.sessionId)
          const response = {
            ...template,
            session_id: recentRequest.sessionId,
            questions: cloneQuestions(template.questions || []),
          }
          debugLog('[Mock Transport] Response (cached):', response)
          return response as T
        }

        const attemptIndex = beginAttempt()
        const preferredSessionId = isEndpointOverridden(API_QUESTIONS_GENERATE)
          ? template.session_id
          : undefined
        const sessionId = preferredSessionId ?? buildSessionId(attemptIndex)
        registerSessionAttempt(sessionId, attemptIndex)

        // Cache this request
        recentGenerateRequests.set(requestKey, { sessionId, timestamp: now })

        const response = {
          ...template,
          session_id: sessionId,
          questions: cloneQuestions(template.questions || []),
        }
        debugLog('[Mock Transport] Response:', response)
        return response as T
    }

    // REQ: REQ-F-B5-Retake-4 - Handle adaptive questions generate endpoint
    if (normalizedUrl === API_QUESTIONS_GENERATE_ADAPTIVE && method === 'POST') {
      debugLog('[Mock Transport] Generating adaptive questions (Round 2) for:', requestData)
      const template = mockData[API_QUESTIONS_GENERATE]
      if (!template) {
        throw new Error('Mock questions response not configured')
      }

      // Generate new session ID for Round 2
      const attemptIndex = beginAttempt()
      const sessionId = buildSessionId(attemptIndex)
      registerSessionAttempt(sessionId, attemptIndex)

      // Return adaptive questions (using same template for simplicity)
      const response = {
        ...template,
        session_id: sessionId,
        questions: cloneQuestions(template.questions || []),
      }
      debugLog('[Mock Transport] Adaptive Response (Round 2):', response)
      return response as T
    }

    // Handle questions autosave endpoint
    if (normalizedUrl === API_QUESTIONS_AUTOSAVE && method === 'POST') {
      debugLog('[Mock Transport] Autosaving answer:', requestData)
      const response = {
        success: true,
        message: 'Answer autosaved successfully',
        autosave_id: `autosave_${Date.now()}`,
        saved_at: new Date().toISOString(),
      }
      debugLog('[Mock Transport] Response:', response)
      return response as T
    }

    // Handle questions score endpoint
    if (normalizedUrl.startsWith(API_QUESTIONS_SCORE) && method === 'POST') {
      debugLog('[Mock Transport] Calculating score for session:', normalizedUrl)
      const response = {
        session_id: requestData?.session_id || 'mock_session_123',
        round: 1,
        score: 85.0,
        correct_count: 4,
        total_count: 5,
        wrong_categories: { 'ML Fundamentals': 1 },
        auto_completed: true,
      }
      debugLog('[Mock Transport] Response:', response)
      return response as T
    }

    // Handle session complete endpoint
    if (normalizedUrl.startsWith(API_SESSION_COMPLETE) && normalizedUrl.includes('/complete') && method === 'POST') {
      // Extract session_id from URL: /api/questions/session/{session_id}/complete
      const sessionIdMatch = normalizedUrl.match(/\/api\/questions\/session\/([^/]+)\/complete/)
      const sessionId = sessionIdMatch ? sessionIdMatch[1] : 'mock_session_123'

      debugLog('[Mock Transport] Completing session:', sessionId)
      const response = {
        status: 'completed',
        session_id: sessionId,
        round: 1,
        message: 'Round 1 session completed successfully',
      }
      debugLog('[Mock Transport] Response:', response)
      return response as T
    }

    // Handle GET /api/questions/explanations/session/{session_id}
    if (normalizedUrl.startsWith(API_QUESTIONS_EXPLANATIONS) && method === 'GET') {
      const sessionIdMatch = normalizedUrl.match(/\/api\/questions\/explanations\/session\/([^/]+)/)
      const sessionId = sessionIdMatch ? sessionIdMatch[1] : 'mock_session_123'

      debugLog('[Mock Transport] Fetching explanations for session:', sessionId)
      const response = {
        explanations: [
          {
            question_id: 'q1',
            question_number: 1,
            question_text: 'What is the primary goal of machine learning?',
            user_answer: 'To replace human intelligence',
            correct_answer: 'To enable computers to learn from data',
            is_correct: false,
            explanation_text:
              '[틀린 이유]\n머신러닝의 주요 목표는 인간 지능을 대체하는 것이 아니라, 데이터로부터 학습하여 패턴을 발견하고 예측하는 것입니다.\n\n[정답의 원리]\n머신러닝은 데이터에서 패턴을 자동으로 학습하여 새로운 데이터에 대한 예측이나 결정을 내릴 수 있게 합니다. 이는 명시적으로 프로그래밍하지 않고도 컴퓨터가 작업을 수행할 수 있게 하는 핵심 기술입니다.\n\n[개념 구분]\n인간 지능 대체는 AGI(Artificial General Intelligence)의 목표이며, 현재 머신러닝은 특정 작업에 특화된 Narrow AI입니다.\n\n[복습 팁]\n머신러닝의 3가지 주요 유형(지도학습, 비지도학습, 강화학습)과 각각의 활용 사례를 정리해보세요.',
            explanation_sections: [
              {
                title: '[틀린 이유]',
                content:
                  '머신러닝의 주요 목표는 인간 지능을 대체하는 것이 아니라, 데이터로부터 학습하여 패턴을 발견하고 예측하는 것입니다.',
              },
              {
                title: '[정답의 원리]',
                content:
                  '머신러닝은 데이터에서 패턴을 자동으로 학습하여 새로운 데이터에 대한 예측이나 결정을 내릴 수 있게 합니다. 이는 명시적으로 프로그래밍하지 않고도 컴퓨터가 작업을 수행할 수 있게 하는 핵심 기술입니다.',
              },
              {
                title: '[개념 구분]',
                content:
                  '인간 지능 대체는 AGI(Artificial General Intelligence)의 목표이며, 현재 머신러닝은 특정 작업에 특화된 Narrow AI입니다.',
              },
              {
                title: '[복습 팁]',
                content:
                  '머신러닝의 3가지 주요 유형(지도학습, 비지도학습, 강화학습)과 각각의 활용 사례를 정리해보세요.',
              },
            ],
            reference_links: [
              {
                title: 'Machine Learning Basics - Stanford CS229',
                url: 'https://cs229.stanford.edu/',
              },
              {
                title: 'Introduction to Machine Learning',
                url: 'https://developers.google.com/machine-learning/crash-course',
              },
              {
                title: 'Machine Learning Mastery',
                url: 'https://machinelearningmastery.com/start-here/',
              },
            ],
          },
          {
            question_id: 'q2',
            question_number: 2,
            question_text: 'Deep learning is a subset of machine learning.',
            user_answer: 'True',
            correct_answer: 'True',
            is_correct: true,
            explanation_text:
              '[정답입니다]\n완벽합니다! 딥러닝은 머신러닝의 하위 분야로, 인공 신경망을 사용하여 복잡한 패턴을 학습합니다.\n\n[핵심 개념]\n딥러닝은 여러 층의 신경망(Deep Neural Networks)을 사용하여 데이터의 계층적 표현을 학습합니다. 이미지 인식, 자연어 처리 등에서 혁신적인 성능을 보여줍니다.\n\n[실무 활용]\nCNN(이미지), RNN/LSTM(시계열), Transformer(자연어) 등 다양한 아키텍처가 실무에서 활용되고 있습니다.',
            explanation_sections: [
              {
                title: '[정답입니다]',
                content:
                  '완벽합니다! 딥러닝은 머신러닝의 하위 분야로, 인공 신경망을 사용하여 복잡한 패턴을 학습합니다.',
              },
              {
                title: '[핵심 개념]',
                content:
                  '딥러닝은 여러 층의 신경망(Deep Neural Networks)을 사용하여 데이터의 계층적 표현을 학습합니다. 이미지 인식, 자연어 처리 등에서 혁신적인 성능을 보여줍니다.',
              },
              {
                title: '[실무 활용]',
                content:
                  'CNN(이미지), RNN/LSTM(시계열), Transformer(자연어) 등 다양한 아키텍처가 실무에서 활용되고 있습니다.',
              },
            ],
            reference_links: [
              {
                title: 'Deep Learning Specialization - Andrew Ng',
                url: 'https://www.coursera.org/specializations/deep-learning',
              },
              {
                title: 'Neural Networks and Deep Learning',
                url: 'http://neuralnetworksanddeeplearning.com/',
              },
              {
                title: 'Deep Learning Book',
                url: 'https://www.deeplearningbook.org/',
              },
            ],
          },
          {
            question_id: 'q3',
            question_number: 3,
            question_text: 'Explain the difference between supervised and unsupervised learning.',
            user_answer: 'Supervised uses labeled data, unsupervised does not.',
            correct_answer: 'Supervised learning uses labeled data, unsupervised learning uses unlabeled data.',
            is_correct: true,
            explanation_text:
              '[정답입니다]\n정확합니다! 지도학습과 비지도학습의 핵심 차이를 잘 이해하고 계십니다.\n\n[핵심 개념]\n지도학습: 입력(X)과 정답(Y)이 함께 제공되어 예측 모델 학습 (예: 분류, 회귀)\n비지도학습: 정답 없이 데이터의 패턴과 구조를 발견 (예: 군집화, 차원축소)\n\n[실무 팁]\n실무에서는 준지도학습(Semi-supervised)도 자주 사용됩니다. 소량의 레이블 데이터와 대량의 비레이블 데이터를 함께 활용합니다.',
            explanation_sections: [
              {
                title: '[정답입니다]',
                content:
                  '정확합니다! 지도학습과 비지도학습의 핵심 차이를 잘 이해하고 계십니다.',
              },
              {
                title: '[핵심 개념]',
                content:
                  '지도학습: 입력(X)과 정답(Y)이 함께 제공되어 예측 모델 학습 (예: 분류, 회귀)\n비지도학습: 정답 없이 데이터의 패턴과 구조를 발견 (예: 군집화, 차원축소)',
              },
              {
                title: '[실무 팁]',
                content:
                  '실무에서는 준지도학습(Semi-supervised)도 자주 사용됩니다. 소량의 레이블 데이터와 대량의 비레이블 데이터를 함께 활용합니다.',
              },
            ],
            reference_links: [
              {
                title: 'Supervised vs Unsupervised Learning',
                url: 'https://www.ibm.com/cloud/blog/supervised-vs-unsupervised-learning',
              },
              {
                title: 'Machine Learning Types Explained',
                url: 'https://towardsdatascience.com/supervised-vs-unsupervised-learning-14f68e32ea8d',
              },
              {
                title: 'Semi-supervised Learning Overview',
                url: 'https://en.wikipedia.org/wiki/Semi-supervised_learning',
              },
            ],
          },
          {
            question_id: 'q4',
            question_number: 4,
            question_text: 'Which algorithm is commonly used for classification tasks?',
            user_answer: 'K-means clustering',
            correct_answer: 'Random Forest',
            is_correct: false,
            explanation_text:
              '[틀린 이유]\nK-means는 비지도학습의 군집화 알고리즘으로, 분류(Classification) 작업이 아닌 클러스터링에 사용됩니다.\n\n[정답의 원리]\nRandom Forest는 여러 개의 결정 트리를 앙상블하여 분류 및 회귀 작업에 사용하는 강력한 지도학습 알고리즘입니다. 과적합을 방지하고 높은 정확도를 제공합니다.\n\n[개념 구분]\n분류(Classification): 지도학습, 정답 레이블 필요 (예: Random Forest, SVM, Logistic Regression)\n군집화(Clustering): 비지도학습, 정답 없이 유사한 데이터 그룹화 (예: K-means, DBSCAN)\n\n[복습 팁]\n분류 알고리즘(Random Forest, SVM, Neural Networks)과 군집화 알고리즘(K-means, Hierarchical Clustering)의 차이를 명확히 구분하세요.',
            explanation_sections: [
              {
                title: '[틀린 이유]',
                content:
                  'K-means는 비지도학습의 군집화 알고리즘으로, 분류(Classification) 작업이 아닌 클러스터링에 사용됩니다.',
              },
              {
                title: '[정답의 원리]',
                content:
                  'Random Forest는 여러 개의 결정 트리를 앙상블하여 분류 및 회귀 작업에 사용하는 강력한 지도학습 알고리즘입니다. 과적합을 방지하고 높은 정확도를 제공합니다.',
              },
              {
                title: '[개념 구분]',
                content:
                  '분류(Classification): 지도학습, 정답 레이블 필요 (예: Random Forest, SVM, Logistic Regression)\n군집화(Clustering): 비지도학습, 정답 없이 유사한 데이터 그룹화 (예: K-means, DBSCAN)',
              },
              {
                title: '[복습 팁]',
                content:
                  '분류 알고리즘(Random Forest, SVM, Neural Networks)과 군집화 알고리즘(K-means, Hierarchical Clustering)의 차이를 명확히 구분하세요.',
              },
            ],
            reference_links: [
              {
                title: 'Random Forest Explained',
                url: 'https://www.analyticsvidhya.com/blog/2021/06/understanding-random-forest/',
              },
              {
                title: 'Classification vs Clustering',
                url: 'https://www.geeksforgeeks.org/difference-between-classification-and-clustering/',
              },
              {
                title: 'Scikit-learn Random Forest',
                url: 'https://scikit-learn.org/stable/modules/ensemble.html#forest',
              },
            ],
          },
          {
            question_id: 'q5',
            question_number: 5,
            question_text: 'What is overfitting and how can you prevent it?',
            user_answer: 'When model performs well on training data but poorly on new data. Use regularization.',
            correct_answer: 'Overfitting occurs when a model learns training data too well, including noise. Prevention: regularization, cross-validation, early stopping, dropout.',
            is_correct: true,
            explanation_text:
              '[정답입니다]\n훌륭합니다! 과적합의 개념과 정규화를 통한 방지 방법을 정확히 이해하고 계십니다.\n\n[핵심 개념]\n과적합(Overfitting): 모델이 훈련 데이터에 과도하게 맞춰져 새로운 데이터에 대한 일반화 성능이 떨어지는 현상\n\n과적합 방지 기법:\n1. 정규화(Regularization): L1, L2 규제로 가중치 크기 제한\n2. 교차 검증(Cross-validation): 여러 검증 세트로 일반화 성능 평가\n3. 조기 종료(Early Stopping): 검증 손실이 증가할 때 학습 중단\n4. 드롭아웃(Dropout): 신경망 학습 시 일부 뉴런 무작위 비활성화\n5. 데이터 증강(Data Augmentation): 훈련 데이터 다양성 증가\n\n[실무 팁]\nHoldout 검증 세트를 항상 유지하여 과적합을 조기에 감지하고, 학습 곡선(Learning Curve)을 그려서 과적합/과소적합 여부를 시각적으로 확인하세요.',
            explanation_sections: [
              {
                title: '[정답입니다]',
                content:
                  '훌륭합니다! 과적합의 개념과 정규화를 통한 방지 방법을 정확히 이해하고 계십니다.',
              },
              {
                title: '[핵심 개념]',
                content:
                  '과적합(Overfitting): 모델이 훈련 데이터에 과도하게 맞춰져 새로운 데이터에 대한 일반화 성능이 떨어지는 현상',
              },
              {
                title: '[과적합 방지 기법]',
                content:
                  '1. 정규화(Regularization): L1, L2 규제로 가중치 크기 제한\n2. 교차 검증(Cross-validation): 여러 검증 세트로 일반화 성능 평가\n3. 조기 종료(Early Stopping): 검증 손실이 증가할 때 학습 중단\n4. 드롭아웃(Dropout): 신경망 학습 시 일부 뉴런 무작위 비활성화\n5. 데이터 증강(Data Augmentation): 훈련 데이터 다양성 증가',
              },
              {
                title: '[실무 팁]',
                content:
                  'Holdout 검증 세트를 항상 유지하여 과적합을 조기에 감지하고, 학습 곡선(Learning Curve)을 그려서 과적합/과소적합 여부를 시각적으로 확인하세요.',
              },
            ],
            reference_links: [
              {
                title: 'Overfitting and Underfitting',
                url: 'https://www.tensorflow.org/tutorials/keras/overfit_and_underfit',
              },
              {
                title: 'Regularization Techniques',
                url: 'https://towardsdatascience.com/regularization-in-machine-learning-76441ddcf99a',
              },
              {
                title: 'Practical Guide to Preventing Overfitting',
                url: 'https://machinelearningmastery.com/introduction-to-regularization-to-reduce-overfitting/',
              },
            ],
          },
        ],
      }
      debugLog('[Mock Transport] Response:', response)
      return response as T
    }

    // Handle GET /profile/nickname endpoint
    if (normalizedUrl === API_PROFILE_NICKNAME && method === 'GET') {
      const response = mockData[API_PROFILE_NICKNAME]
      debugLog('[Mock Transport] Response:', response)
      return response as T
    }

    // Handle GET /profile/consent endpoint
    if (normalizedUrl === API_PROFILE_CONSENT && method === 'GET') {
      const response = mockData[API_PROFILE_CONSENT]
      debugLog('[Mock Transport] Response:', response)
      return response as T
    }

    // REQ: REQ-F-B5-Retake-1 - Handle GET /profile/history endpoint
    if (normalizedUrl === API_PROFILE_HISTORY && method === 'GET') {
      const response = mockData[API_PROFILE_HISTORY]
      debugLog('[Mock Transport] GET /profile/history - Response:', response)
      return response as T
    }

    // REQ: REQ-F-A1-Home - Handle GET /api/profile/last-test-result endpoint
    if (normalizedUrl === API_PROFILE_LAST_TEST_RESULT && method === 'GET') {
      const response = mockData[API_PROFILE_LAST_TEST_RESULT]
      debugLog('[Mock Transport] Response:', response)
      return response as T
    }

    // REQ: REQ-F-A1-Home - Handle GET /api/statistics/total-participants endpoint
    if (normalizedUrl === API_STATISTICS_TOTAL_PARTICIPANTS && method === 'GET') {
      const response = mockData[API_STATISTICS_TOTAL_PARTICIPANTS]
      debugLog('[Mock Transport] Response:', response)
      return response as T
    }

    // Handle GET /profile/ranking endpoint
    if (normalizedUrl === API_PROFILE_RANKING && method === 'GET') {
      if (hasMockOverride(normalizedUrl)) {
        const override = mockData[normalizedUrl]
        debugLog('[Mock Transport] Response (override):', override)
        return override as T
      }

      // Use the most recent session's result or generate a new one
      const mostRecentAttempt = sessionSequenceCounter || 1
      let result = Array.from(sessionResultsCache.values()).pop()

      if (!result) {
        result = getResultForAttempt(mostRecentAttempt)
        const sessionId = buildSessionId(mostRecentAttempt)
        sessionResultsCache.set(sessionId, result)
        recordCompletedResult(mostRecentAttempt, result)
      }

      debugLog('[Mock Transport] Response (ranking):', result)
      return deepClone(result) as T
    }

      // Handle GET /api/results/{sessionId} endpoint
      if (normalizedUrl.startsWith('/api/results/') && method === 'GET') {
        if (normalizedUrl === API_RESULTS_PREVIOUS) {
          if (hasMockOverride(normalizedUrl)) {
            const override = mockData[normalizedUrl]
            debugLog('[Mock Transport] Response (override):', override)
            return override as T
          }
          debugLog('[Mock Transport] Response (previous):', nextPreviousResult)
          return (nextPreviousResult ?? null) as T
        }

        if (hasMockOverride(normalizedUrl)) {
          const override = mockData[normalizedUrl]
          debugLog('[Mock Transport] Response (override):', override)
          return override as T
        }

        const sessionId = normalizedUrl.split('/').pop()
        if (sessionId && sessionId !== 'previous') {
          const attemptIndex = resolveAttemptIndex(sessionId)
          let result = sessionResultsCache.get(sessionId)

          if (!result) {
            result = getResultForAttempt(attemptIndex)
            sessionResultsCache.set(sessionId, result)
            recordCompletedResult(attemptIndex, result)
          }

          debugLog('[Mock Transport] Response:', result)
          return deepClone(result) as T
        }
      }

    // Find mock data for this endpoint
    const data = mockData[normalizedUrl]

    if (typeof data === 'undefined') {
      throw new Error(`Mock data not found for: ${normalizedUrl}`)
    }

    debugLog('[Mock Transport] Response:', data)
    return data as T
  }

  async get<T>(url: string, _config?: RequestConfig): Promise<T> {
    return this.mockRequest<T>(url, 'GET')
  }

  async post<T>(url: string, data?: any, _config?: RequestConfig): Promise<T> {
    return this.mockRequest<T>(url, 'POST', data)
  }

  async put<T>(url: string, data?: any, _config?: RequestConfig): Promise<T> {
    return this.mockRequest<T>(url, 'PUT', data)
  }

  async delete<T>(url: string, _config?: RequestConfig): Promise<T> {
    return this.mockRequest<T>(url, 'DELETE')
  }
}

export const mockTransport = new MockTransport()

// Helper to update mock data at runtime
export function setMockData(endpoint: string, data: any) {
  const normalized = ensureApiPath(endpoint)
  mockData[normalized] = data
  overriddenEndpoints.add(normalized)
}

// Helper to read mock data (useful for assertions in tests)
export function getMockData(endpoint: string) {
  return mockData[ensureApiPath(endpoint)]
}

export function getMockRequests(filter?: { url?: string; method?: string }) {
  return requestLog.filter((entry) => {
    if (filter?.url && ensureApiPath(filter.url) !== entry.url) {
      return false
    }
    if (filter?.method && filter.method.toUpperCase() !== entry.method.toUpperCase()) {
      return false
    }
    return true
  })
}

export function clearMockRequests() {
  requestLog.length = 0
}

export function setMockError(endpoint: string, message: string) {
  endpointErrors.set(ensureApiPath(endpoint), message)
}

export function clearMockErrors(endpoint?: string) {
  if (endpoint) {
    endpointErrors.delete(ensureApiPath(endpoint))
  } else {
    endpointErrors.clear()
  }
}

export function resetMockResults() {
  resetResultProgression()
}

// Helper to simulate different scenarios
export function setMockScenario(
  scenario: 'no-nickname' | 'has-nickname' | 'no-consent' | 'has-consent' | 'no-survey' | 'has-survey' | 'error' | 'reset-results' | 'no-test-result' | 'has-test-result'
) {
  switch (scenario) {
    case 'no-nickname':
      mockData[API_PROFILE_NICKNAME].nickname = null
      mockConfig.simulateError = false
      break
    case 'has-nickname':
      mockData[API_PROFILE_NICKNAME].nickname = 'mockuser'
      mockData[API_PROFILE_NICKNAME].registered_at = '2025-11-11T00:00:00Z'
      mockData[API_PROFILE_NICKNAME].updated_at = '2025-11-11T00:00:00Z'
      mockConfig.simulateError = false
      break
    case 'no-consent':
      mockData[API_PROFILE_CONSENT] = {
        consented: false,
        consent_at: null,
      }
      mockConfig.simulateError = false
      break
    case 'has-consent':
      mockData[API_PROFILE_CONSENT] = {
        consented: true,
        consent_at: '2025-11-18T00:00:00Z',
      }
      mockConfig.simulateError = false
      break
    case 'no-survey':
      mockData[API_PROFILE_SURVEY] = {
        level: null,
        career: null,
        job_role: null,
        duty: null,
        interests: null,
      }
      mockConfig.simulateError = false
      break
    case 'has-survey':
      mockData[API_PROFILE_SURVEY] = {
        level: 'intermediate',
        career: 5,
        job_role: 'SW',
        duty: 'Backend Development',
        interests: ['AI', 'Backend'],
      }
      mockConfig.simulateError = false
      break
    case 'error':
      mockConfig.simulateError = true
      break
    case 'reset-results':
      resetMockResults()
      mockConfig.simulateError = false
      break
    case 'no-test-result':
      mockData[API_PROFILE_LAST_TEST_RESULT] = {
        hasResult: false,
        grade: null,
        completedAt: null,
        badgeUrl: null,
      }
      mockConfig.simulateError = false
      break
    case 'has-test-result':
      mockData[API_PROFILE_LAST_TEST_RESULT] = {
        hasResult: true,
        grade: 3,
        completedAt: '2025-01-15',
        badgeUrl: null,
      }
      mockConfig.simulateError = false
      break
  }
  debugLog(`[Mock Transport] Scenario set to: ${scenario}`)
}
