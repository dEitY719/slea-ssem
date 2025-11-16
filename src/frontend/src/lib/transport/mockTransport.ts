// Mock HTTP transport for development without backend

import { HttpTransport, RequestConfig } from './types'

const API_AUTH_LOGIN = '/api/auth/login'
const API_PROFILE_NICKNAME = '/api/profile/nickname'
const API_PROFILE_NICKNAME_CHECK = '/api/profile/nickname/check'
const API_PROFILE_REGISTER = '/api/profile/register'
const API_PROFILE_SURVEY = '/api/profile/survey'
const API_QUESTIONS_GENERATE = '/api/questions/generate'
const API_QUESTIONS_AUTOSAVE = '/api/questions/autosave'
const API_RESULTS_PREVIOUS = '/api/results/previous'

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
  [API_PROFILE_SURVEY]: {
    level: null,
    career: null,
    job_role: null,
    duty: null,
    interests: null,
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
      saved: true,
      session_id: 'mock_session_123',
      question_id: '',
      saved_at: new Date().toISOString(),
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
      { grade: 'Intermediate-Advanced', count: 76, percentage: 15.0 },
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
      { grade: 'Intermediate-Advanced', count: 138, percentage: 27.3 },
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
}

const overriddenEndpoints = new Set<string>()

// Track taken nicknames for mock: 이미 사용 중인 닉네임 목록
const takenNicknames = new Set(['admin', 'test', 'mockuser', 'existing_user'])

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
    console.log(`[Mock Transport] ${method} ${normalizedUrl}`, requestData)

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
        console.log('[Mock Transport] Response:', response)
        return response as T
      }

    // Handle nickname check endpoint
    if (normalizedUrl === API_PROFILE_NICKNAME_CHECK && method === 'POST' && requestData?.nickname) {
      const nickname = requestData.nickname
      const isTaken = takenNicknames.has(nickname.toLowerCase())

      const response = {
        available: !isTaken,
        suggestions: isTaken ? [
          `${nickname}_1`,
          `${nickname}_2`,
          `${nickname}_3`
        ] : []
      }

      console.log('[Mock Transport] Response:', response)
      return response as T
    }

      // Handle nickname register endpoint
    if (normalizedUrl === API_PROFILE_REGISTER && method === 'POST' && requestData?.nickname) {
      const nickname: string = requestData.nickname

      if (nickname.length < 3) {
        throw new Error('닉네임은 3자 이상이어야 합니다.')
      }

      if (nickname.length > 30) {
        throw new Error('닉네임은 30자 이하여야 합니다.')
      }

      const validPattern = /^[a-zA-Z0-9_]+$/
      if (!validPattern.test(nickname)) {
        throw new Error('닉네임은 영문자, 숫자, 언더스코어만 사용 가능합니다.')
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

      console.log('[Mock Transport] Response:', response)
      return response as T
    }

    // Handle survey update endpoint
    if (normalizedUrl === API_PROFILE_SURVEY && method === 'PUT') {
      const validLevels = ['beginner', 'intermediate', 'advanced']

      // Validate level if provided
      if (requestData?.level && !validLevels.includes(requestData.level)) {
        throw new Error('Invalid level. Must be one of: beginner, intermediate, advanced')
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

      console.log('[Mock Transport] Survey updated:', mockData[API_PROFILE_SURVEY])
      console.log('[Mock Transport] Response:', response)
      return response as T
    }

    // Handle questions generate endpoint
    if (normalizedUrl === API_QUESTIONS_GENERATE && method === 'POST') {
      console.log('[Mock Transport] Generating questions for:', requestData)
        const template = mockData[API_QUESTIONS_GENERATE]
        if (!template) {
          throw new Error('Mock questions response not configured')
        }

        const attemptIndex = beginAttempt()
        const preferredSessionId = isEndpointOverridden(API_QUESTIONS_GENERATE)
          ? template.session_id
          : undefined
        const sessionId = preferredSessionId ?? buildSessionId(attemptIndex)
        registerSessionAttempt(sessionId, attemptIndex)
        const response = {
          ...template,
          session_id: sessionId,
          questions: cloneQuestions(template.questions || []),
        }
        console.log('[Mock Transport] Response:', response)
        return response as T
    }

    // Handle questions autosave endpoint
    if (normalizedUrl === API_QUESTIONS_AUTOSAVE && method === 'POST') {
      console.log('[Mock Transport] Autosaving answer:', requestData)
      const response = {
        saved: true,
        session_id: requestData?.session_id || 'mock_session_123',
        question_id: requestData?.question_id || '',
        saved_at: new Date().toISOString(),
      }
      console.log('[Mock Transport] Response:', response)
      return response as T
    }

    // Handle GET /profile/nickname endpoint
    if (normalizedUrl === API_PROFILE_NICKNAME && method === 'GET') {
      const response = mockData[API_PROFILE_NICKNAME]
      console.log('[Mock Transport] Response:', response)
      return response as T
    }

      // Handle GET /api/results/{sessionId} endpoint
      if (normalizedUrl.startsWith('/api/results/') && method === 'GET') {
        if (normalizedUrl === API_RESULTS_PREVIOUS) {
          if (hasMockOverride(normalizedUrl)) {
            const override = mockData[normalizedUrl]
            console.log('[Mock Transport] Response (override):', override)
            return override as T
          }
          console.log('[Mock Transport] Response (previous):', nextPreviousResult)
          return (nextPreviousResult ?? null) as T
        }

        if (hasMockOverride(normalizedUrl)) {
          const override = mockData[normalizedUrl]
          console.log('[Mock Transport] Response (override):', override)
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

          console.log('[Mock Transport] Response:', result)
          return deepClone(result) as T
        }
      }

    // Find mock data for this endpoint
    const data = mockData[normalizedUrl]

    if (typeof data === 'undefined') {
      throw new Error(`Mock data not found for: ${normalizedUrl}`)
    }

    console.log('[Mock Transport] Response:', data)
    return data as T
  }

  async get<T>(url: string, config?: RequestConfig): Promise<T> {
    return this.mockRequest<T>(url, 'GET')
  }

  async post<T>(url: string, data?: any, config?: RequestConfig): Promise<T> {
    return this.mockRequest<T>(url, 'POST', data)
  }

  async put<T>(url: string, data?: any, config?: RequestConfig): Promise<T> {
    return this.mockRequest<T>(url, 'PUT', data)
  }

  async delete<T>(url: string, config?: RequestConfig): Promise<T> {
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
  scenario: 'no-nickname' | 'has-nickname' | 'no-survey' | 'has-survey' | 'error' | 'reset-results'
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
  }
  console.log(`[Mock Transport] Scenario set to: ${scenario}`)
}
