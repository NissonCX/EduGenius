/**
 * API 客户端 - 带自动刷新 Token 功能
 *
 * 功能：
 * - 自动携带认证头
 * - 自动检测 401 错误并刷新 Token
 * - 自动重试失败的请求
 * - 防止并发刷新请求
 */

import { getApiUrl } from './config'
import { dispatchAuthLogout } from './auth-events'

interface RefreshTokenResponse {
  access_token: string
  refresh_token?: string
}

let isRefreshing = false
let failedQueue: Array<{
  resolve: (value: any) => void
  reject: (reason: any) => void
}> = []

/**
 * 处理等待中的请求
 */
function processQueue(error: any, token: string | null = null) {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })

  failedQueue = []
}

/**
 * 刷新 Access Token
 */
async function refreshAccessToken(): Promise<string> {
  const refreshToken = localStorage.getItem('refresh_token')

  if (!refreshToken) {
    throw new Error('No refresh token available')
  }

  const response = await fetch(getApiUrl('/api/users/refresh-token'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ refresh_token: refreshToken })
  })

  if (!response.ok) {
    throw new Error('Failed to refresh token')
  }

  const data: RefreshTokenResponse = await response.json()

  // 更新存储的 tokens
  localStorage.setItem('token', data.access_token)
  if (data.refresh_token) {
    localStorage.setItem('refresh_token', data.refresh_token)
  }

  return data.access_token
}

/**
 * 带自动刷新的 fetch 函数
 */
export async function fetchWithAuth(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  // 添加认证头
  const token = localStorage.getItem('token')
  const authHeaders: HeadersInit = {
    'Content-Type': 'application/json',
  }

  if (token) {
    authHeaders['Authorization'] = `Bearer ${token}`
  }

  const requestOptions: RequestInit = {
    ...options,
    headers: {
      ...authHeaders,
      ...options.headers,
    },
  }

  // 发起请求
  let response = await fetch(url, requestOptions)

  // 如果是 401 错误，尝试刷新 Token
  if (response.status === 401 && token) {
    if (isRefreshing) {
      // 如果正在刷新，将请求加入队列
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject })
      })
        .then(newToken => {
          // 重试原请求
          const retryOptions: RequestInit = {
            ...options,
            headers: {
              ...requestOptions.headers,
              'Authorization': `Bearer ${newToken}`,
            },
          }
          return fetch(url, retryOptions)
        })
        .catch(err => {
          return Promise.reject(err)
        })
    }

    isRefreshing = true

    try {
      // 刷新 Token
      const newToken = await refreshAccessToken()

      // 处理队列中的请求
      processQueue(null, newToken)

      // 重试原请求
      const retryOptions: RequestInit = {
        ...options,
        headers: {
          ...requestOptions.headers,
          'Authorization': `Bearer ${newToken}`,
        },
      }
      response = await fetch(url, retryOptions)

    } catch (error) {
      // 刷新失败，清除 tokens 并跳转到登录页
      processQueue(error, null)

      // 触发登出事件（通知所有组件更新UI并显示提示）
      dispatchAuthLogout('token_refresh_failed')

      // 清除 tokens
      localStorage.removeItem('token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')

      // 延迟跳转，让组件有时间显示提示
      if (typeof window !== 'undefined') {
        setTimeout(() => {
          window.location.href = '/login'
        }, 100)
      }

      throw error
    } finally {
      isRefreshing = false
    }
  }

  return response
}

/**
 * 带超时和认证的 fetch 函数
 */
export async function fetchWithAuthAndTimeout(
  url: string,
  options: RequestInit = {},
  timeout: number = 10000
): Promise<Response> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout)

  try {
    const response = await fetchWithAuth(url, {
      ...options,
      signal: controller.signal
    })
    clearTimeout(timeoutId)
    return response
  } catch (error) {
    clearTimeout(timeoutId)
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error(`请求超时 (${timeout / 1000}秒)`)
    }
    throw error
  }
}
