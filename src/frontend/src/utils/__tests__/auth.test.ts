// REQ: REQ-F-A1-2
import { describe, it, expect, beforeEach } from 'vitest'
import { saveToken, getToken, removeToken } from '../auth'

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString()
    },
    removeItem: (key: string) => {
      delete store[key]
    },
    clear: () => {
      store = {}
    },
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

describe('Auth Utility Functions - REQ-F-A1-2', () => {
  beforeEach(() => {
    localStorageMock.clear()
  })

  describe('saveToken', () => {
    // Test 1: Happy Path - 토큰 저장
    it('should save token to localStorage', () => {
      const token = 'test_jwt_token_123'
      saveToken(token)

      expect(localStorageMock.getItem('slea_ssem_token')).toBe(token)
    })

    // Test 2: Edge Case - 긴 토큰
    it('should save long token string', () => {
      const longToken = 'a'.repeat(1000)
      saveToken(longToken)

      expect(localStorageMock.getItem('slea_ssem_token')).toBe(longToken)
    })
  })

  describe('getToken', () => {
    // Test 4: Happy Path - 저장된 토큰 조회
    it('should retrieve saved token from localStorage', () => {
      const token = 'saved_token_456'
      localStorageMock.setItem('slea_ssem_token', token)

      const retrieved = getToken()

      expect(retrieved).toBe(token)
    })

    // Test 5: Edge Case - 토큰이 없을 때
    it('should return null when no token exists', () => {
      const retrieved = getToken()

      expect(retrieved).toBeNull()
    })
  })

  describe('removeToken', () => {
    // Test 6: Happy Path - 토큰 삭제
    it('should remove token from localStorage', () => {
      localStorageMock.setItem('slea_ssem_token', 'token_to_remove')

      removeToken()

      expect(localStorageMock.getItem('slea_ssem_token')).toBeNull()
    })

    // Test 7: Edge Case - 토큰이 없을 때 삭제 시도
    it('should not throw error when removing non-existent token', () => {
      expect(() => removeToken()).not.toThrow()
    })

    // Test 8: Mock mode flag should also be removed
    it('should remove mock mode flag when removing token', () => {
      localStorageMock.setItem('slea_ssem_token', 'mock_jwt_token_123')
      localStorageMock.setItem('slea_ssem_api_mock', 'true')

      removeToken()

      expect(localStorageMock.getItem('slea_ssem_token')).toBeNull()
      expect(localStorageMock.getItem('slea_ssem_api_mock')).toBeNull()
    })
  })

  describe('Token lifecycle', () => {
    // Test 9: Acceptance Criteria - 저장 → 조회 → 삭제 전체 흐름
    it('should handle complete token lifecycle', () => {
      // 1. 저장
      const token = 'lifecycle_token_789'
      saveToken(token)
      expect(getToken()).toBe(token)

      // 2. 조회
      const retrieved = getToken()
      expect(retrieved).toBe(token)

      // 3. 삭제
      removeToken()
      expect(getToken()).toBeNull()
    })
  })
})
