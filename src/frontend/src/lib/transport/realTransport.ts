// Real HTTP transport using fetch API
// REQ: REQ-F-A1-6, REQ-B-A1 (HttpOnly cookie authentication), REQ-F-A0-API

import { HttpTransport, RequestConfig } from './types'

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
    // REQ-F-A0-API-2, REQ-F-A0-API-3: Private APIs include credentials
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

      // REQ-F-A0-API-3: Private-Auth + 401 → Auto redirect to /sso
      if ((accessLevel === 'private-auth' || accessLevel === 'private-member') && response.status === 401) {
        console.warn('[Auth] 401 Unauthorized - redirecting to /sso')
        window.location.href = '/sso'
        // Return never-resolving promise (page will redirect anyway)
        return new Promise(() => {}) as Promise<T>
      }

      // REQ-F-A0-API-4: Private-Member + 403 + code=NEED_SIGNUP → Auto redirect to /signup
      if (accessLevel === 'private-member' && response.status === 403 && error.code === 'NEED_SIGNUP') {
        console.warn('[Auth] 403 Signup Required - redirecting to /signup')
        window.location.href = '/signup'
        return new Promise(() => {}) as Promise<T>
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
