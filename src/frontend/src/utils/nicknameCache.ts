const CACHE_KEY = 'slea_ssem_cached_nickname'

export function getCachedNickname(): string | null {
  if (typeof window === 'undefined') {
    return null
  }
  return localStorage.getItem(CACHE_KEY)
}

export function setCachedNickname(nickname: string | null): void {
  if (typeof window === 'undefined') {
    return
  }
  if (nickname === null) {
    localStorage.removeItem(CACHE_KEY)
  } else {
    localStorage.setItem(CACHE_KEY, nickname)
  }
}

export function clearCachedNickname(): void {
  if (typeof window === 'undefined') {
    return
  }
  localStorage.removeItem(CACHE_KEY)
}
