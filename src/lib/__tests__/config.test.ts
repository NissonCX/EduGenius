/**
 * Config 模块单元测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { getApiUrl, fetchWithTimeout, getAuthHeadersSimple } from '../config'

describe('Config 模块', () => {
  const originalEnv = process.env

  beforeEach(() => {
    // 重置环境变量
    process.env = { ...originalEnv }
    vi.clearAllMocks()
  })

  afterEach(() => {
    process.env = originalEnv
  })

  describe('getApiUrl', () => {
    it('应该使用默认的 localhost:8000', () => {
      delete process.env.NEXT_PUBLIC_API_URL
      expect(getApiUrl('/api/test')).toBe('http://localhost:8000/api/test')
    })

    it('应该使用环境变量中的 API URL', () => {
      process.env.NEXT_PUBLIC_API_URL = 'https://api.example.com'
      expect(getApiUrl('/api/test')).toBe('https://api.example.com/api/test')
    })

    it('应该移除 URL 尾部的斜杠', () => {
      process.env.NEXT_PUBLIC_API_URL = 'https://api.example.com/'
      expect(getApiUrl('/api/test')).toBe('https://api.example.com/api/test')
    })

    it('应该处理不以斜杠开头的路径', () => {
      expect(getApiUrl('api/test')).toBe('http://localhost:8000/api/test')
    })
  })

  describe('fetchWithTimeout', () => {
    beforeEach(() => {
      global.fetch = vi.fn()
    })

    it('应该在超时时间内成功返回响应', async () => {
      const mockResponse = { ok: true, json: async () => ({ data: 'test' }) }
      vi.mocked(fetch).mockResolvedValue(mockResponse as any)

      const result = await fetchWithTimeout('http://test.com', {}, 5000)

      expect(result).toEqual(mockResponse)
      expect(fetch).toHaveBeenCalledTimes(1)
    })

    it('应该在超时后抛出错误', async () => {
      vi.mocked(fetch).mockImplementation(
        () =>
          new Promise(() => {
            // 永不解决的 Promise
          }) as any
      )

      await expect(
        fetchWithTimeout('http://test.com', {}, 100)
      ).rejects.toThrow('请求超时 (0.1秒)')
    })

    it('应该使用 AbortController 中止请求', async () => {
      const abortSpy = vi.spyOn(AbortController.prototype, 'abort')
      vi.mocked(fetch).mockImplementation(
        () =>
          new Promise(() => {}) as any
      )

      try {
        await fetchWithTimeout('http://test.com', {}, 100)
      } catch (e) {
        // 预期的超时错误
      }

      expect(abortSpy).toHaveBeenCalled()
    })

    it('应该在请求失败时抛出错误', async () => {
      const networkError = new Error('Network error')
      vi.mocked(fetch).mockRejectedValue(networkError)

      await expect(
        fetchWithTimeout('http://test.com')
      ).rejects.toThrow('Network error')
    })
  })

  describe('getAuthHeadersSimple', () => {
    beforeEach(() => {
      // Mock localStorage
      Object.defineProperty(global, 'localStorage', {
        value: {
          getItem: vi.fn(),
          setItem: vi.fn()
        },
        writable: true
      })
    })

    it('应该包含默认的 Content-Type', () => {
      const headers = getAuthHeadersSimple()
      expect(headers).toEqual({
        'Content-Type': 'application/json'
      })
    })

    it('应该从 localStorage 读取 token', () => {
      vi.mocked(localStorage.getItem).mockReturnValue('test-token')

      const headers = getAuthHeadersSimple()

      expect(localStorage.getItem).toHaveBeenCalledWith('token')
      expect(headers).toEqual({
        'Content-Type': 'application/json',
        'Authorization': 'Bearer test-token'
      })
    })

    it('应该支持不包含 Content-Type', () => {
      vi.mocked(localStorage.getItem).mockReturnValue('test-token')

      const headers = getAuthHeadersSimple(false)

      expect(headers).toEqual({
        'Authorization': 'Bearer test-token'
      })
      expect(headers).not.toHaveProperty('Content-Type')
    })

    it('在没有 token 时仍然包含 Content-Type', () => {
      vi.mocked(localStorage.getItem).mockReturnValue(null)

      const headers = getAuthHeadersSimple()

      expect(headers).toEqual({
        'Content-Type': 'application/json'
      })
    })
  })
})
