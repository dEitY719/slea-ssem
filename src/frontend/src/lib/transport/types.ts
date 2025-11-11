// Transport interface for API requests

export interface RequestConfig {
  headers?: Record<string, string>
  body?: any
}

export interface HttpTransport {
  get<T>(url: string, config?: RequestConfig): Promise<T>
  post<T>(url: string, data?: any, config?: RequestConfig): Promise<T>
  put<T>(url: string, data?: any, config?: RequestConfig): Promise<T>
  delete<T>(url: string, config?: RequestConfig): Promise<T>
}
