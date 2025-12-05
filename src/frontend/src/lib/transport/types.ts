// Transport interface for API requests

// REQ-F-A0-API: API Access Levels
export type ApiAccessLevel = 'public' | 'private-auth' | 'private-member'

export interface RequestConfig {
  headers?: Record<string, string>
  body?: any
  accessLevel?: ApiAccessLevel // Default: 'private-member'
}

export interface HttpTransport {
  get<T>(url: string, config?: RequestConfig): Promise<T>
  post<T>(url: string, data?: any, config?: RequestConfig): Promise<T>
  put<T>(url: string, data?: any, config?: RequestConfig): Promise<T>
  delete<T>(url: string, config?: RequestConfig): Promise<T>
}
