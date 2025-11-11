// Mock API responses for development without backend

/**
 * Mock data for GET /api/profile/nickname
 *
 * To test different scenarios, change the nickname value:
 * - null: User hasn't set nickname (will redirect to /signup)
 * - 'mockuser': User has nickname (will proceed to next step)
 */
export const mockUserProfile = {
  user_id: 'mock_user@samsung.com',
  nickname: null as string | null,  // Change this to test different scenarios
  registered_at: null as string | null,
  updated_at: null as string | null,
}

/**
 * Mock API handler - returns mock data after simulated delay
 */
export async function getMockResponse<T>(
  endpoint: string,
  delay = 500
): Promise<T | null> {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, delay))

  // Route to appropriate mock data
  if (endpoint.includes('/profile/nickname')) {
    return mockUserProfile as T
  }

  // Add more mock endpoints here as needed
  // if (endpoint.includes('/other-endpoint')) { ... }

  return null
}

/**
 * Enable/disable specific mock scenarios
 */
export const mockScenarios = {
  // Change these to test different scenarios
  userHasNickname: false,  // If true, mockUserProfile.nickname = 'mockuser'
  simulateError: false,     // If true, throw error instead of returning data
  slowNetwork: false,       // If true, add extra delay (3s)
}

// Apply mock scenarios
if (mockScenarios.userHasNickname) {
  mockUserProfile.nickname = 'mockuser'
  mockUserProfile.registered_at = '2025-11-11T00:00:00Z'
  mockUserProfile.updated_at = '2025-11-11T00:00:00Z'
}
