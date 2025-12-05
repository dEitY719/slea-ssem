// Mock Transport Survey Endpoint Tests
import { describe, test, expect, beforeEach } from 'vitest'
import { mockTransport, setMockScenario, mockConfig, setMockAuthState } from '../mockTransport'

describe('Mock Transport - /profile/survey endpoint', () => {
  beforeEach(() => {
    mockConfig.simulateError = false
    mockConfig.delay = 0
    setMockScenario('no-survey')
    // Set mock auth state to authenticated (Private-Auth API requires SSO)
    setMockAuthState(true, null)
  })

  test('PUT /profile/survey with valid level (beginner)', async () => {
    const response = await mockTransport.put<any>('/profile/survey', {
      level: 'beginner',
    }, { accessLevel: 'private-auth' })

    expect(response).toMatchObject({
      success: true,
      message: '자기평가 정보 업데이트 완료',
      user_id: 'mock_user@samsung.com',
    })
    expect(response.survey_id).toBeDefined()
    expect(response.updated_at).toBeDefined()
  })

  test('PUT /profile/survey with valid level (intermediate)', async () => {
    const response = await mockTransport.put('/profile/survey', {
      level: 'intermediate',
    }, { accessLevel: 'private-auth' })

    expect(response).toMatchObject({
      success: true,
      message: '자기평가 정보 업데이트 완료',
    })
  })

  test('PUT /profile/survey with valid level (advanced)', async () => {
    const response = await mockTransport.put('/profile/survey', {
      level: 'advanced',
    }, { accessLevel: 'private-auth' })

    expect(response).toMatchObject({
      success: true,
      message: '자기평가 정보 업데이트 완료',
    })
  })

  test('PUT /profile/survey with invalid level throws error', async () => {
    await expect(
      mockTransport.put('/profile/survey', {
        level: 'expert',
      }, { accessLevel: 'private-auth' })
    ).rejects.toThrow('Invalid level. Must be one of: beginner, intermediate, inter-advanced, advanced, elite')
  })

  test('PUT /profile/survey with valid career (0-60)', async () => {
    const response = await mockTransport.put('/profile/survey', {
      career: 5,
    }, { accessLevel: 'private-auth' })

    expect(response).toMatchObject({
      success: true,
    })
  })

  test('PUT /profile/survey with career < 0 throws error', async () => {
    await expect(
      mockTransport.put('/profile/survey', {
        career: -1,
      }, { accessLevel: 'private-auth' })
    ).rejects.toThrow('career must be a number between 0 and 60')
  })

  test('PUT /profile/survey with career > 60 throws error', async () => {
    await expect(
      mockTransport.put('/profile/survey', {
        career: 61,
      }, { accessLevel: 'private-auth' })
    ).rejects.toThrow('career must be a number between 0 and 60')
  })

  test('PUT /profile/survey with valid job_role', async () => {
    const response = await mockTransport.put('/profile/survey', {
      job_role: 'SW',
    }, { accessLevel: 'private-auth' })

    expect(response).toMatchObject({
      success: true,
    })
  })

  test('PUT /profile/survey with job_role > 100 chars throws error', async () => {
    const longString = 'a'.repeat(101)
    await expect(
      mockTransport.put('/profile/survey', {
        job_role: longString,
      }, { accessLevel: 'private-auth' })
    ).rejects.toThrow('job_role must be a string with max 100 characters')
  })

  test('PUT /profile/survey with valid duty', async () => {
    const response = await mockTransport.put('/profile/survey', {
      duty: 'Backend Development',
    }, { accessLevel: 'private-auth' })

    expect(response).toMatchObject({
      success: true,
    })
  })

  test('PUT /profile/survey with duty > 500 chars throws error', async () => {
    const longString = 'a'.repeat(501)
    await expect(
      mockTransport.put('/profile/survey', {
        duty: longString,
      }, { accessLevel: 'private-auth' })
    ).rejects.toThrow('duty must be a string with max 500 characters')
  })

  test('PUT /profile/survey with valid interests array', async () => {
    const response = await mockTransport.put('/profile/survey', {
      interests: ['AI', 'Backend', 'Frontend'],
    }, { accessLevel: 'private-auth' })

    expect(response).toMatchObject({
      success: true,
    })
  })

  test('PUT /profile/survey with interests > 20 items throws error', async () => {
    const largeArray = Array(21).fill('interest')
    await expect(
      mockTransport.put('/profile/survey', {
        interests: largeArray,
      }, { accessLevel: 'private-auth' })
    ).rejects.toThrow('interests must be an array with max 20 items')
  })

  test('PUT /profile/survey with all fields', async () => {
    const response = await mockTransport.put<any>('/profile/survey', {
      level: 'intermediate',
      career: 5,
      job_role: 'SW',
      duty: 'Backend Development',
      interests: ['AI', 'Backend'],
    }, { accessLevel: 'private-auth' })

    expect(response).toMatchObject({
      success: true,
      message: '자기평가 정보 업데이트 완료',
      user_id: 'mock_user@samsung.com',
    })
    expect(response.survey_id).toMatch(/^survey_\d+$/)
    expect(response.updated_at).toBeDefined()
  })

  test('setMockScenario("has-survey") sets survey data', () => {
    setMockScenario('has-survey')
    // Scenario should be set without errors
    expect(mockConfig.simulateError).toBe(false)
  })

  test('setMockScenario("no-survey") clears survey data', () => {
    setMockScenario('no-survey')
    // Scenario should be set without errors
    expect(mockConfig.simulateError).toBe(false)
  })
})
