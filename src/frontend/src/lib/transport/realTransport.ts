// Real HTTP transport using fetch API

import { HttpTransport, RequestConfig } from './types'
import { getToken } from '../../utils/auth'

class RealTransport implements HttpTransport {
  private async request<T>(
    url: string,
    method: string,
    config?: RequestConfig
  ): Promise<T> {
    const token = getToken()

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...config?.headers,
    }

    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const fetchConfig: RequestInit = {
      method,
      headers,
    }

    if (config?.body) {
      fetchConfig.body = JSON.stringify(config.body)
    }

    const response = await fetch(url, fetchConfig)

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: `HTTP ${response.status}`
      }))
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
