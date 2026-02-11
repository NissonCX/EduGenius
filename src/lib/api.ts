/**
 * 统一的 API 客户端工具
 *
 * 功能:
 * - 统一的请求超时控制
 * - 自动错误处理
 * - 统一的响应格式化
 * - 请求重试机制
 */

import { getApiUrl, fetchWithTimeout, getAuthHeadersSimple } from './config'

export interface ApiError {
  message: string
  status?: number
  code?: string
}

/**
 * 统一的 API 请求配置
 */
interface ApiRequestConfig {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  headers?: HeadersInit
  body?: any
  timeout?: number
  retries?: number
}

/**
 * 统一的 API 响应格式
 */
interface ApiResponse<T = any> {
  data: T
  status: number
  ok: boolean
}

/**
 * API 客户端类
 */
class ApiClient {
  private defaultTimeout = 10000 // 10秒默认超时
  private defaultRetries = 1 // 默认重试次数

  /**
   * 发送 API 请求
   */
  async request<T = any>(
    endpoint: string,
    config: ApiRequestConfig = {}
  ): Promise<ApiResponse<T>> {
    const {
      method = 'GET',
      headers = {},
      body,
      timeout = this.defaultTimeout,
      retries = this.defaultRetries
    } = config

    const url = getApiUrl(endpoint)

    // 构建请求头
    const requestHeaders: HeadersInit = {
      ...getAuthHeadersSimple(method !== 'GET'),
      ...headers
    }

    // 构建请求选项
    const requestOptions: RequestInit = {
      method,
      headers: requestHeaders
    }

    // 添加请求体（非 GET 请求）
    if (body && method !== 'GET') {
      requestOptions.body = typeof body === 'string' ? body : JSON.stringify(body)
    }

    // 发送请求（带重试）
    let lastError: Error | null = null
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const response = await fetchWithTimeout(url, requestOptions, timeout)

        // 处理响应
        if (response.ok) {
          const data = await response.json()
          return {
            data,
            status: response.status,
            ok: true
          }
        }

        // 处理错误响应
        const errorData = await response.json().catch(() => ({ detail: response.statusText }))
        throw new ApiErrorClass(
          errorData.detail || errorData.message || '请求失败',
          response.status,
          errorData.code
        )

      } catch (error) {
        lastError = error as Error

        // 如果是最后一次尝试或不可重试的错误，直接抛出
        if (attempt === retries || this.isNonRetryableError(error)) {
          break
        }

        // 等待一段时间后重试（指数退避）
        await this.delay(Math.pow(2, attempt) * 1000)
      }
    }

    // 所有重试都失败
    throw lastError || new ApiErrorClass('请求失败')
  }

  /**
   * GET 请求
   */
  async get<T = any>(endpoint: string, config: Omit<ApiRequestConfig, 'method'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'GET' })
  }

  /**
   * POST 请求
   */
  async post<T = any>(endpoint: string, data?: any, config: Omit<ApiRequestConfig, 'method' | 'body'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'POST', body: data })
  }

  /**
   * PUT 请求
   */
  async put<T = any>(endpoint: string, data?: any, config: Omit<ApiRequestConfig, 'method' | 'body'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'PUT', body: data })
  }

  /**
   * DELETE 请求
   */
  async delete<T = any>(endpoint: string, config: Omit<ApiRequestConfig, 'method'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'DELETE' })
  }

  /**
   * PATCH 请求
   */
  async patch<T = any>(endpoint: string, data?: any, config: Omit<ApiRequestConfig, 'method' | 'body'> = {}): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'PATCH', body: data })
  }

  /**
   * 判断是否为不可重试的错误
   */
  private isNonRetryableError(error: any): boolean {
    // 4xx 错误（除了 429）通常不应该重试
    if (error instanceof ApiErrorClass) {
      const status = error.status
      return status !== undefined && status >= 400 && status < 500 && status !== 429
    }
    return false
  }

  /**
   * 延迟函数
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }
}

/**
 * API 错误类
 */
class ApiErrorClass extends Error implements ApiError {
  status?: number
  code?: string

  constructor(message: string, status?: number, code?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

// 导出单例实例
export const apiClient = new ApiClient()

// 导出错误类
export { ApiErrorClass }

/**
 * 快捷方法
 */
export const api = {
  get: <T = any>(endpoint: string, config?: Omit<ApiRequestConfig, 'method'>) => apiClient.get<T>(endpoint, config),
  post: <T = any>(endpoint: string, data?: any, config?: Omit<ApiRequestConfig, 'method' | 'body'>) => apiClient.post<T>(endpoint, data, config),
  put: <T = any>(endpoint: string, data?: any, config?: Omit<ApiRequestConfig, 'method' | 'body'>) => apiClient.put<T>(endpoint, data, config),
  delete: <T = any>(endpoint: string, config?: Omit<ApiRequestConfig, 'method'>) => apiClient.delete<T>(endpoint, config),
  patch: <T = any>(endpoint: string, data?: any, config?: Omit<ApiRequestConfig, 'method' | 'body'>) => apiClient.patch<T>(endpoint, data, config),
}
