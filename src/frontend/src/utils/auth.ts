// REQ: REQ-F-A1-2
/**
 * Authentication utility functions for token management.
 *
 * Handles JWT token storage, retrieval, and removal using localStorage.
 */

const TOKEN_KEY = 'slea_ssem_token'

/**
 * Save JWT token to localStorage.
 *
 * @param token - JWT token string to save
 */
export const saveToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token)
}

/**
 * Retrieve JWT token from localStorage.
 *
 * @returns JWT token string or null if not found
 */
export const getToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY)
}

/**
 * Remove JWT token from localStorage.
 * Also clears mock mode flag if present.
 */
export const removeToken = (): void => {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem('slea_ssem_api_mock')
}
