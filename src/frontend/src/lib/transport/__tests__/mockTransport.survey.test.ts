// Mock Transport Survey Endpoint Tests
import { describe, test, expect, beforeEach } from 'vitest'
import { mockTransport, setMockScenario, mockConfig, setMockAuthState } from '../mockTransport'

const PRIVATE_AUTH_CONFIG = { accessLevel: 'private-auth' } as const
const putPrivateAuth = <T>(url: string, data?: any) =>
  mockTransport.put<T>(url, data, PRIVATE_AUTH_CONFIG)

describe('Mock Transport - /profile/survey endpoint', () => {
  beforeEach(() => {
    mockConfig.simulateError = false
    mockConfig.delay = 0
    setMockScenario('no-survey')
    // Set mock auth state to authenticated (Private-Auth API requires SSO)
    setMockAuthState(true, null)
  })

  test('PUT /profile/survey with valid level (beginner)', async () => {
    const response = await putPrivateAuth<any>('/profile/survey', {
      level: 'beginner',
    })

    expect(response).toMatchObject({
      success: true,
      message: '자기평가 정보 업데이트 완료',
      user_id: 'mock_user@samsung.com',
    })
    expect(response.survey_id).toBeDefined()
    expect(response.updated_at).toBeDefined()
  })

  test('PUT /profile/survey with valid level (intermediate)', async () => {
    const response = await putPrivateAuth('/profile/survey', {
      level: 'intermediate',
    })

    expect(response).toMatchObject({
      success: true,
      message: '자기평가 정보 업데이트 완료',
    })
  })

  test('PUT /profile/survey with valid level (advanced)', async () => {
    const response = await putPrivateAuth('/profile/survey', {
      level: 'advanced',
    })

    expect(response).toMatchObject({
      success: true,
      message: '자기평가 정보 업데이트 완료',
    })
  })

  test('PUT /profile/survey with invalid level throws error', async () => {
    await expect(
      putPrivateAuth('/profile/survey', {
        level: 'expert',
      })
    ).rejects.toThrow('Invalid level. Must be one of: beginner, intermediate, inter-advanced, advanced, elite')
  })

  test('PUT /profile/survey with valid career (0-60)', async () => {
    const response = await putPrivateAuth('/profile/survey', {
      career: 5,
    })

    expect(response).toMatchObject({
      success: true,
    })
  })

  test('PUT /profile/survey with career < 0 throws error', async () => {
    await expect(
      putPrivateAuth('/profile/survey', {
        career: -1,
      })
    ).rejects.toThrow('career must be a number between 0 and 60')
  })

  test('PUT /profile/survey with career > 60 throws error', async () => {
    await expect(
      putPrivateAuth('/profile/survey', {
        career: 61,
      })
    ).rejects.toThrow('career must be a number between 0 and 60')
  })

  test('PUT /profile/survey with valid job_role', async () => {
    const response = await putPrivateAuth('/profile/survey', {
      job_role: 'SW',
    })

    expect(response).toMatchObject({
      success: true,
    })
  })

  test('PUT /profile/survey with job_role > 100 chars throws error', async () => {
    const longString = 'a'.repeat(101)
    await expect(
      putPrivateAuth('/profile/survey', {
        job_role: longString,
      })
    ).rejects.toThrow('job_role must be a string with max 100 characters')
  })

  test('PUT /profile/survey with valid duty', async () => {
    const response = await putPrivateAuth('/profile/survey', {
      duty: 'Backend Development',
    })

    expect(response).toMatchObject({
      success: true,
    })
  })

  test('PUT /profile/survey with duty > 500 chars throws error', async () => {
    const longString = 'a'.repeat(501)
    await expect(
      putPrivateAuth('/profile/survey', {
        duty: longString,
      })
    ).rejects.toThrow('duty must be a string with max 500 characters')
  })

  test('PUT /profile/survey with valid interests array', async () => {
    const response = await putPrivateAuth('/profile/survey', {
      interests: ['AI', 'Backend', 'Frontend'],
    })

    expect(response).toMatchObject({
      success: true,
    })
  })

  test('PUT /profile/survey with interests > 20 items throws error', async () => {
    const largeArray = Array(21).fill('interest')
    await expect(
      putPrivateAuth('/profile/survey', {
        interests: largeArray,
      })
    ).rejects.toThrow('interests must be an array with max 20 items')
  })

  test('PUT /profile/survey with all fields', async () => {
    const response = await putPrivateAuth<any>('/profile/survey', {
      level: 'intermediate',
      career: 5,
      job_role: 'SW',
      duty: 'Backend Development',
      interests: ['AI', 'Backend'],
    })

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
