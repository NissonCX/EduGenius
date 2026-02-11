/**
 * API 错误处理工具
 */

export interface ApiError {
  message: string
  status?: number
  code?: string
  details?: any
}

/**
 * 标准 API 错误类
 */
export class StandardError extends Error {
  status: number
  code?: string
  details?: any

  constructor(message: string, status: number = 500, code?: string, details?: any) {
    super(message)
    this.name = 'StandardError'
    this.status = status
    this.code = code
    this.details = details
  }
}

/**
 * 处理 fetch API 错误
 */
export async function handleFetchError(response: Response): Promise<never> {
  let errorMessage = '请求失败'
  let errorDetails: any

  try {
    const data = await response.json()
    errorMessage = data.detail || data.message || errorMessage
    errorDetails = data
  } catch {
    errorMessage = response.statusText || errorMessage
  }

  throw new StandardError(
    errorMessage,
    response.status,
    response.status.toString(),
    errorDetails
  )
}

/**
 * 处理 API 请求的通用错误
 */
export function handleApiError(error: unknown): ApiError {
  if (error instanceof StandardError) {
    return {
      message: error.message,
      status: error.status,
      code: error.code,
      details: error.details
    }
  }

  if (error instanceof Error) {
    return {
      message: error.message,
      status: 500,
      code: 'UNKNOWN_ERROR'
    }
  }

  return {
    message: '发生未知错误',
    status: 500,
    code: 'UNKNOWN_ERROR'
  }
}

/**
 * 获取用户友好的错误消息
 */
export function getFriendlyErrorMessage(error: ApiError): string {
  // 根据错误状态码返回友好消息
  switch (error.status) {
    case 400:
      return '请求参数有误，请检查后重试'
    case 401:
      return '请先登录'
    case 403:
      return '您没有权限执行此操作'
    case 404:
      return '请求的资源不存在'
    case 429:
      return '请求过于频繁，请稍后再试'
    case 500:
      return '服务器错误，请稍后重试'
    case 503:
      return '服务暂时不可用，请稍后重试'
    default:
      return error.message || '发生错误，请稍后重试'
  }
}

/**
 * 创建带错误处理的 fetch 包装器
 */
export async function safeFetch(
  url: string,
  options?: RequestInit
): Promise<Response> {
  try {
    const response = await fetch(url, options)

    if (!response.ok) {
      await handleFetchError(response)
    }

    return response
  } catch (error) {
    if (error instanceof StandardError) {
      throw error
    }

    // 网络错误或其他错误
    throw new StandardError(
      '网络连接失败，请检查网络后重试',
      0,
      'NETWORK_ERROR'
    )
  }
}

/**
 * 错误日志记录
 */
export function logError(error: unknown, context?: string) {
  const errorInfo = handleApiError(error)

  console.error(`[Error${context ? ` - ${context}` : ''}]`, {
    message: errorInfo.message,
    status: errorInfo.status,
    code: errorInfo.code,
    details: errorInfo.details,
    timestamp: new Date().toISOString()
  })

  // 这里可以添加远程日志服务
  // sendToErrorTracking(errorInfo, context)
}

/**
 * 显示错误提示（可以集成 toast 通知）
 */
export function showErrorToast(error: unknown, context?: string) {
  const errorInfo = handleApiError(error)
  const friendlyMessage = getFriendlyErrorMessage(errorInfo)

  // 记录错误
  logError(error, context)

  // 这里可以集成 toast 通知库
  // toast.error(friendlyMessage)

  // 临时使用 alert（生产环境应使用 toast）
  if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
    alert(friendlyMessage)
  }
}
