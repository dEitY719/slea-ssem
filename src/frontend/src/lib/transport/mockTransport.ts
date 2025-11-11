// Mock HTTP transport for development without backend

import { HttpTransport, RequestConfig } from './types'

// Mock data storage
const mockData: Record<string, any> = {
  '/api/profile/nickname': {
    user_id: 'mock_user@samsung.com',
    nickname: null,  // Change to 'mockuser' to test nickname exists
    registered_at: null,
    updated_at: null,
  },
  '/profile/nickname/check': {
    available: true,
    suggestions: [],
  },
  // Add more mock endpoints here
}

// Track taken nicknames for mock
const takenNicknames = new Set(['admin', 'test', 'mockuser', 'existing_user'])

// Mock configuration
export const mockConfig = {
  delay: 500,           // Network delay in ms
  simulateError: false, // Simulate API errors
  slowNetwork: false,   // Simulate slow network (3s delay)
}

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
    if (url === '/profile/register' && method === 'POST' && requestData?.nickname) {
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
export function setMockScenario(scenario: 'no-nickname' | 'has-nickname' | 'error') {
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
    case 'error':
      mockConfig.simulateError = true
      break
  }
  console.log(`[Mock Transport] Scenario set to: ${scenario}`)
}
