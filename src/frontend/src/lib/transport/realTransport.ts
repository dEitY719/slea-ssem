// Real HTTP transport using fetch API
// REQ: REQ-F-A1-6, REQ-B-A1 (HttpOnly cookie authentication), REQ-F-A0-API

import { HttpTransport, RequestConfig } from './types'

const buildReturnToParam = (): string => {
  if (typeof window === 'undefined') {
    return encodeURIComponent('/')
  }
  const { pathname, search, hash } = window.location
  return encodeURIComponent(`${pathname}${search}${hash}`)
}

class RealTransport implements HttpTransport {
  private async request<T>(
    url: string,
    method: string,
    config?: RequestConfig
  ): Promise<T> {
    // REQ-F-A0-API: Default access level is 'private-member'
    const accessLevel = config?.accessLevel ?? 'private-member'

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...config?.headers,
    }

    const fetchConfig: RequestInit = {
      method,
      headers,
    }

    // REQ-F-A0-API-1: Public API does not include credentials
    // REQ-F-A0-API-2: Private APIs include credentials
    if (accessLevel !== 'public') {
      fetchConfig.credentials = 'include' // Include HttpOnly cookies
    }

    if (config?.body) {
      fetchConfig.body = JSON.stringify(config.body)
    }

    const response = await fetch(url, fetchConfig)

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: `HTTP ${response.status}`,
        code: null
      }))

      // REQ-F-A0-API-3: 401 + NEED_SSO → Auto redirect to /sso with returnTo
      if (response.status === 401 && error.code === 'NEED_SSO') {
        console.warn('[Auth] 401 NEED_SSO - redirecting to /sso')
        const returnTo = buildReturnToParam()
        window.location.href = `/sso?returnTo=${returnTo}`
        return new Promise(() => {}) as Promise<T>
      }

      // REQ-F-A0-API-4: 401 + NEED_LOGIN → Auto redirect to /login with returnTo
      if (response.status === 401 && error.code === 'NEED_LOGIN') {
        console.warn('[Auth] 401 NEED_LOGIN - redirecting to /login')
        const returnTo = buildReturnToParam()
        window.location.href = `/login?returnTo=${returnTo}`
        return new Promise(() => {}) as Promise<T>
      }

      // REQ-F-A0-API-5: 403 + NEED_SIGNUP → Auto redirect to /signup with returnTo
      if (response.status === 403 && error.code === 'NEED_SIGNUP') {
        console.warn('[Auth] 403 NEED_SIGNUP - redirecting to /signup')
        const returnTo = buildReturnToParam()
        window.location.href = `/signup?returnTo=${returnTo}`
        return new Promise(() => {}) as Promise<T>
      }

      // REQ-F-A0-API-6: 403 + FORBIDDEN → Forbidden
      if (response.status === 403 && error.code === 'FORBIDDEN') {
        const errorMessage = error.detail || 'Forbidden'
        throw new Error(errorMessage)
      }

      // Other errors - throw for page to handle
      const errorMessage = error.detail || `HTTP ${response.status}`
      throw new Error(errorMessage)
    }

    return response.json()
  }

  async get<T>(url: string, config?: RequestConfig): Promise<T> {
    return this.request<T>(url, 'GET', config)
  }

  async post<T>(url: string, data?: any, config?: RequestConfig): Promise<T> {
    return this.request<T>(url, 'POST', {
      ...config,
      body: data,
    })
  }

  async put<T>(url: string, data?: any, config?: RequestConfig): Promise<T> {
    return this.request<T>(url, 'PUT', {
      ...config,
      body: data,
    })
  }

  async delete<T>(url: string, config?: RequestConfig): Promise<T> {
    return this.request<T>(url, 'DELETE', config)
  }
}

export const realTransport = new RealTransport()
