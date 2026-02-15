/**
 * API URL 配置
 * 独立文件避免循环依赖
 */

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

/**
 * 获取完整的 API URL
 */
export function getApiUrl(path: string): string {
  const baseUrl = API_BASE_URL.replace(/\/$/, '') // 移除尾部斜杠
  const apiPath = path.startsWith('/') ? path : `/${path}`
  return `${baseUrl}${apiPath}`
}
