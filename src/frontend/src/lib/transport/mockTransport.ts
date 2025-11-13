// Mock HTTP transport for development without backend

import { HttpTransport, RequestConfig } from './types'

// Mock data storage: 엔드포인트별로 미리 정의된 가짜 데이터 저장
const mockData: Record<string, any> = {
  '/api/profile/nickname': {
    user_id: 'mock_user@samsung.com',
    nickname: null,  // Change to 'mockuser' to test nickname exists
    registered_at: null,
    updated_at: null,
  },
  '/api/profile/nickname/check': {
    available: true,
    suggestions: [],
  },
  '/profile/survey': {
    level: null,
    career: null,
    job_role: null,
    duty: null,
    interests: null,
  },
  '/questions/generate': {
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
  '/questions/autosave': {
    saved: true,
    session_id: 'mock_session_123',
    question_id: '',
    saved_at: new Date().toISOString(),
  },
  // Add more mock endpoints here
}

// Track taken nicknames for mock: 이미 사용 중인 닉네임 목록
const takenNicknames = new Set(['admin', 'test', 'mockuser', 'existing_user'])

// Mock configuration: 네트워크 지연, 에러 여부 등 시뮬레이션 설정
export const mockConfig = {
  delay: 500,           // Network delay in ms
  simulateError: false, // Simulate API errors
  slowNetwork: false,   // Simulate slow network (3s delay)
}

// 실제로 요청을 처리하는 객체
class MockTransport implements HttpTransport {
  private async mockRequest<T>(url: string, method: string, requestData?: any): Promise<T> {
    console.log(`[Mock Transport] ${method} ${url}`, requestData)

    // Simulate network delay
    const delay = mockConfig.slowNetwork ? 3000 : mockConfig.delay
    await new Promise(resolve => setTimeout(resolve, delay))

    // Simulate error
    if (mockConfig.simulateError) {
      throw new Error('Mock Transport: Simulated API error')
    }

    // Handle nickname check endpoint
    if (url === '/profile/nickname/check' && method === 'POST' && requestData?.nickname) {
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
    if (url === '/api/profile/register' && method === 'POST' && requestData?.nickname) {
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
      mockData['/api/profile/nickname'] = {
        ...mockData['/api/profile/nickname'],
        nickname,
        registered_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      const response = {
        success: true,
        message: '닉네임 등록 완료',
        user_id: 'mock_user@samsung.com',
        nickname,
        registered_at: mockData['/api/profile/nickname'].registered_at,
      }

      console.log('[Mock Transport] Response:', response)
      return response as T
    }

    // Handle survey update endpoint
    if (url === '/api/profile/survey' && method === 'PUT') {
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
      mockData['/profile/survey'] = {
        ...mockData['/profile/survey'],
        ...requestData,
      }

      const response = {
        success: true,
        message: '자기평가 정보 업데이트 완료',
        user_id: 'mock_user@samsung.com',
        survey_id: `survey_${Date.now()}`,
        updated_at: new Date().toISOString(),
      }

      console.log('[Mock Transport] Survey updated:', mockData['/profile/survey'])
      console.log('[Mock Transport] Response:', response)
      return response as T
    }

    // Handle questions generate endpoint
    if (url === '/api/questions/generate' && method === 'POST') {
      console.log('[Mock Transport] Generating questions for:', requestData)
      const response = mockData['/questions/generate']
      console.log('[Mock Transport] Response:', response)
      return response as T
    }

    // Handle questions autosave endpoint
    if (url === '/api/questions/autosave' && method === 'POST') {
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
    if (url === '/profile/nickname' && method === 'GET') {
      const response = mockData['/api/profile/nickname']
      console.log('[Mock Transport] Response:', response)
      return response as T
    }

    // Handle GET /api/results/{sessionId} endpoint
    if (url.startsWith('/api/results/') && method === 'GET') {
      const sessionId = url.split('/').pop()
      console.log('[Mock Transport] Fetching results for session:', sessionId)

      // Mock result data (REQ: REQ-F-B4-1, REQ-F-B4-3)
      const mockResultData = {
        user_id: 1,
        grade: 'Advanced',
        score: 82.5,
        rank: 3,
        total_cohort_size: 506,
        percentile: 72.0,
        percentile_confidence: 'high',
        percentile_description: '상위 28%',
        // REQ: REQ-F-B4-3 - Grade distribution data
        grade_distribution: [
          { grade: 'Beginner', count: 102, percentage: 20.2 },
          { grade: 'Intermediate', count: 156, percentage: 30.8 },
          { grade: 'Intermediate-Advanced', count: 98, percentage: 19.4 },
          { grade: 'Advanced', count: 95, percentage: 18.8 },
          { grade: 'Elite', count: 55, percentage: 10.8 },
        ],
      }

      console.log('[Mock Transport] Response:', mockResultData)
      return mockResultData as T
    }

    // Find mock data for this endpoint
    const data = mockData[url]

    if (!data) {
      throw new Error(`Mock data not found for: ${url}`)
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
  mockData[endpoint] = data
}

// Helper to simulate different scenarios
export function setMockScenario(
  scenario: 'no-nickname' | 'has-nickname' | 'no-survey' | 'has-survey' | 'error'
) {
  switch (scenario) {
    case 'no-nickname':
      mockData['/api/profile/nickname'].nickname = null
      mockConfig.simulateError = false
      break
    case 'has-nickname':
      mockData['/api/profile/nickname'].nickname = 'mockuser'
      mockData['/api/profile/nickname'].registered_at = '2025-11-11T00:00:00Z'
      mockData['/api/profile/nickname'].updated_at = '2025-11-11T00:00:00Z'
      mockConfig.simulateError = false
      break
    case 'no-survey':
      mockData['/profile/survey'] = {
        level: null,
        career: null,
        job_role: null,
        duty: null,
        interests: null,
      }
      mockConfig.simulateError = false
      break
    case 'has-survey':
      mockData['/profile/survey'] = {
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
  }
  console.log(`[Mock Transport] Scenario set to: ${scenario}`)
}
