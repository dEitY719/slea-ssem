// Mock Transport Nickname Validation Tests
// REQ: REQ-F-A2-3, REQ-F-A2-5

import { describe, test, expect, beforeEach } from 'vitest'
import { mockTransport, mockConfig } from '../mockTransport'
import type { NicknameCheckResponse, NicknameRegisterResponse } from '../../../services/profileService'

describe('Mock Transport - Nickname Validation (REQ-F-A2-5)', () => {
  beforeEach(() => {
    mockConfig.simulateError = false
    mockConfig.delay = 0
  })

  describe('1. Length Validation Tests', () => {
    test('POST /profile/nickname/check - 닉네임 너무 짧음 (2자)', async () => {
      await expect(
        mockTransport.post('/profile/nickname/check', { nickname: 'ab' })
      ).rejects.toThrow('닉네임은 3자 이상이어야 합니다.')
    })

    test('POST /profile/nickname/check - 닉네임 너무 김 (31자)', async () => {
      const longNickname = 'a'.repeat(31)
      await expect(
        mockTransport.post('/profile/nickname/check', { nickname: longNickname })
      ).rejects.toThrow('닉네임은 30자 이하여야 합니다.')
    })

    test('POST /profile/nickname/check - 유효한 길이 (3자)', async () => {
      const response = await mockTransport.post('/profile/nickname/check', { nickname: 'abc' })
      expect(response).toHaveProperty('available')
      expect(response).toHaveProperty('suggestions')
    })

    test('POST /profile/nickname/check - 유효한 길이 (30자)', async () => {
      const validNickname = 'a'.repeat(30)
      const response = await mockTransport.post('/profile/nickname/check', { nickname: validNickname })
      expect(response).toHaveProperty('available')
    })
  })

  describe('2. Format Validation Tests', () => {
    test('POST /profile/nickname/check - 특수문자 포함 (@)', async () => {
      await expect(
        mockTransport.post('/profile/nickname/check', { nickname: 'name@email' })
      ).rejects.toThrow('닉네임은 영문자, 숫자, 언더스코어만 사용 가능합니다.')
    })

    test('POST /profile/nickname/check - 특수문자 포함 (-)', async () => {
      await expect(
        mockTransport.post('/profile/nickname/check', { nickname: 'my-name' })
      ).rejects.toThrow('닉네임은 영문자, 숫자, 언더스코어만 사용 가능합니다.')
    })

    test('POST /profile/nickname/check - 공백 포함', async () => {
      await expect(
        mockTransport.post('/profile/nickname/check', { nickname: 'my name' })
      ).rejects.toThrow('닉네임은 영문자, 숫자, 언더스코어만 사용 가능합니다.')
    })

    test('POST /profile/nickname/check - 유효한 형식 (영문+숫자+언더스코어)', async () => {
      const response = await mockTransport.post<NicknameCheckResponse>('/profile/nickname/check', { nickname: 'player_123' })
      expect(response).toHaveProperty('available')
      expect(response.available).toBe(true)
    })

    test('POST /profile/nickname/check - 유효한 형식 (언더스코어만)', async () => {
      const response = await mockTransport.post('/profile/nickname/check', { nickname: 'my_name_here' })
      expect(response).toHaveProperty('available')
    })
  })

  describe('3. Banned Words Validation Tests (REQ-F-A2-5 핵심)', () => {
    test('POST /profile/nickname/check - 금칙어 exact match (admin)', async () => {
      await expect(
        mockTransport.post('/profile/nickname/check', { nickname: 'admin' })
      ).rejects.toThrow("'admin'은(는) 사용할 수 없는 닉네임입니다. 다른 닉네임을 선택해주세요.")
    })

    test('POST /profile/nickname/check - 금칙어 exact match (root)', async () => {
      await expect(
        mockTransport.post('/profile/nickname/check', { nickname: 'root' })
      ).rejects.toThrow("'root'은(는) 사용할 수 없는 닉네임입니다. 다른 닉네임을 선택해주세요.")
    })

    test('POST /profile/nickname/check - 금칙어 exact match (moderator)', async () => {
      await expect(
        mockTransport.post('/profile/nickname/check', { nickname: 'moderator' })
      ).rejects.toThrow("'moderator'은(는) 사용할 수 없는 닉네임입니다. 다른 닉네임을 선택해주세요.")
    })

    test('POST /profile/nickname/check - 금칙어 exact match (bot)', async () => {
      await expect(
        mockTransport.post('/profile/nickname/check', { nickname: 'bot' })
      ).rejects.toThrow("'bot'은(는) 사용할 수 없는 닉네임입니다. 다른 닉네임을 선택해주세요.")
    })

    test('POST /profile/nickname/check - 금칙어로 시작 (admin123)', async () => {
      await expect(
        mockTransport.post('/profile/nickname/check', { nickname: 'admin123' })
      ).rejects.toThrow('닉네임에 사용할 수 없는 단어가 포함되어 있습니다. 다른 닉네임을 선택해주세요.')
    })

    test('POST /profile/nickname/check - 금칙어로 시작 (system_user)', async () => {
      await expect(
        mockTransport.post('/profile/nickname/check', { nickname: 'system_user' })
      ).rejects.toThrow('닉네임에 사용할 수 없는 단어가 포함되어 있습니다. 다른 닉네임을 선택해주세요.')
    })

    test('POST /profile/nickname/check - 대소문자 무관 (ADMIN)', async () => {
      await expect(
        mockTransport.post('/profile/nickname/check', { nickname: 'ADMIN' })
      ).rejects.toThrow("'ADMIN'은(는) 사용할 수 없는 닉네임입니다. 다른 닉네임을 선택해주세요.")
    })

    test('POST /profile/nickname/check - 대소문자 무관 (Admin)', async () => {
      await expect(
        mockTransport.post('/profile/nickname/check', { nickname: 'Admin' })
      ).rejects.toThrow("'Admin'은(는) 사용할 수 없는 닉네임입니다. 다른 닉네임을 선택해주세요.")
    })

    test('POST /profile/nickname/check - 여러 금칙어 테스트', async () => {
      const bannedWords = ['test', 'guest', 'anonymous', 'staff', 'support']

      for (const word of bannedWords) {
        await expect(
          mockTransport.post('/profile/nickname/check', { nickname: word })
        ).rejects.toThrow(`'${word}'은(는) 사용할 수 없는 닉네임입니다. 다른 닉네임을 선택해주세요.`)
      }
    })
  })

  describe('4. Integration Tests', () => {
    test('POST /profile/nickname/check - 유효한 닉네임 + 중복 없음', async () => {
      const response = await mockTransport.post('/profile/nickname/check', { nickname: 'validuser' })

      expect(response).toEqual({
        available: true,
        suggestions: [],
      })
    })

    test('POST /profile/nickname/check - 유효한 닉네임 + 중복 있음', async () => {
      const response = await mockTransport.post('/profile/nickname/check', { nickname: 'mockuser' })

      expect(response).toEqual({
        available: false,
        suggestions: ['mockuser_1', 'mockuser_2', 'mockuser_3'],
      })
    })

    test('POST /profile/nickname/check - 유효한 닉네임 + 중복 있음 (existing_user)', async () => {
      const response = await mockTransport.post<NicknameCheckResponse>('/profile/nickname/check', { nickname: 'existing_user' })

      expect(response.available).toBe(false)
      expect(response.suggestions).toHaveLength(3)
    })
  })

  describe('5. Register Endpoint Tests', () => {
    test('POST /profile/register - 금칙어 등록 시도 (admin)', async () => {
      await expect(
        mockTransport.post('/profile/register', { nickname: 'admin' })
      ).rejects.toThrow("'admin'은(는) 사용할 수 없는 닉네임입니다. 다른 닉네임을 선택해주세요.")
    })

    test('POST /profile/register - 금칙어로 시작하는 닉네임 등록 시도', async () => {
      await expect(
        mockTransport.post('/profile/register', { nickname: 'bot_user' })
      ).rejects.toThrow('닉네임에 사용할 수 없는 단어가 포함되어 있습니다. 다른 닉네임을 선택해주세요.')
    })

    test('POST /profile/register - 너무 짧은 닉네임 등록 시도', async () => {
      await expect(
        mockTransport.post('/profile/register', { nickname: 'ab' })
      ).rejects.toThrow('닉네임은 3자 이상이어야 합니다.')
    })

    test('POST /profile/register - 특수문자 포함 닉네임 등록 시도', async () => {
      await expect(
        mockTransport.post('/profile/register', { nickname: 'name@123' })
      ).rejects.toThrow('닉네임은 영문자, 숫자, 언더스코어만 사용 가능합니다.')
    })

    test('POST /profile/register - 유효한 닉네임 등록 성공', async () => {
      const response = await mockTransport.post<NicknameRegisterResponse>('/profile/register', { nickname: 'newuser123' })

      expect(response).toMatchObject({
        success: true,
        message: '닉네임 등록 완료',
        user_id: 'mock_user@samsung.com',
        nickname: 'newuser123',
      })
      expect(response.registered_at).toBeDefined()
    })
  })

  describe('6. Error Message Clarity Tests (REQ-F-A2-5 Acceptance)', () => {
    test('금칙어 거부 시 명확한 사유 제공 - exact match', async () => {
      try {
        await mockTransport.post('/profile/nickname/check', { nickname: 'admin' })
        throw new Error('Should have thrown validation error')
      } catch (error) {
        const errorMessage = (error as Error).message
        expect(errorMessage).toContain('admin')
        expect(errorMessage).toContain('사용할 수 없는')
        expect(errorMessage).toContain('다른 닉네임을 선택해주세요')
      }
    })

    test('금칙어 거부 시 명확한 사유 제공 - starts with', async () => {
      try {
        await mockTransport.post('/profile/nickname/check', { nickname: 'moderator_main' })
        throw new Error('Should have thrown validation error')
      } catch (error) {
        const errorMessage = (error as Error).message
        expect(errorMessage).toContain('사용할 수 없는 단어')
        expect(errorMessage).toContain('포함')
        expect(errorMessage).toContain('다른 닉네임을 선택해주세요')
      }
    })

    test('형식 오류 시 명확한 사유 제공', async () => {
      try {
        await mockTransport.post('/profile/nickname/check', { nickname: 'my-name' })
        throw new Error('Should have thrown validation error')
      } catch (error) {
        const errorMessage = (error as Error).message
        expect(errorMessage).toContain('영문자')
        expect(errorMessage).toContain('숫자')
        expect(errorMessage).toContain('언더스코어')
      }
    })
  })
})
