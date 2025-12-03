// Real HTTP transport using fetch API
// REQ: REQ-F-A1-6, REQ-B-A1 (HttpOnly cookie authentication), REQ-F-A0-API

import { HttpTransport, RequestConfig } from './types'

// REQ-F-A0-API: Custom error types for access control
export class UnauthorizedError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'UnauthorizedError'
  }
}

export class SignupRequiredError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'SignupRequiredError'
  }
}

export class MembershipRequiredError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'MembershipRequiredError'
  }
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

      // REQ-F-A0-API-3: Private-Auth + 401 → UnauthorizedError (redirect to /sso)
      if (accessLevel === 'private-auth' && response.status === 401) {
        throw new UnauthorizedError(error.detail || 'Authentication required')
      }

      // REQ-F-A0-API-4: Private-Member + 401 → UnauthorizedError (redirect to /sso)
      if (accessLevel === 'private-member' && response.status === 401) {
        throw new UnauthorizedError(error.detail || 'Authentication required')
      }

      // REQ-F-A0-API-4: Private-Member + 403 + code=NEED_SIGNUP → SignupRequiredError
      if (accessLevel === 'private-member' && response.status === 403) {
        if (error.code === 'NEED_SIGNUP') {
          throw new SignupRequiredError(error.detail || 'Signup required')
        }
        throw new MembershipRequiredError(error.detail || 'Member registration required')
      }

      throw new Error(error.detail || 'Request failed')
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
