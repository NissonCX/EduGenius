/**
 * Cache 模块单元测试
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { cache, CacheConfigs, generateCacheKey } from '../cache'

// Mock localStorage
const localStorageMock = {
  store: new Map<string, string>(),
  getItem: (key: string) => localStorageMock.store.get(key) || null,
  setItem: (key: string, value: string) => {
    localStorageMock.store.set(key, value)
  },
  removeItem: (key: string) => {
    localStorageMock.store.delete(key)
  },
  clear: () => {
    localStorageMock.store.clear()
  }
}

Object.defineProperty(global, 'localStorage', {
  value: localStorageMock
})

describe('DataCache', () => {
  beforeEach(() => {
    cache.clear()
    localStorageMock.store.clear()
  })

  describe('基本功能', () => {
    it('应该能够设置和获取缓存', () => {
      const testData = { id: 1, name: 'Test' }
      cache.set('test-key', testData)
      expect(cache.get('test-key')).toEqual(testData)
    })

    it('应该在缓存不存在时返回 null', () => {
      expect(cache.get('non-existent')).toBeNull()
    })

    it('应该能够删除缓存', () => {
      cache.set('test-key', { data: 'test' })
      cache.delete('test-key')
      expect(cache.get('test-key')).toBeNull()
    })

    it('应该能够清空所有缓存', () => {
      cache.set('key1', { data: 'test1' })
      cache.set('key2', { data: 'test2' })
      cache.clear()
      expect(cache.get('key1')).toBeNull()
      expect(cache.get('key2')).toBeNull()
    })
  })

  describe('TTL 过期机制', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })

    afterEach(() => {
      vi.useRealTimers()
    })

    it('应该在 TTL 过期后返回 null', () => {
      cache.set('test-key', { data: 'test' }, { ttl: 1000 })
      expect(cache.get('test-key')).toEqual({ data: 'test' })

      vi.advanceTimersByTime(1001)
      expect(cache.get('test-key')).toBeNull()
    })

    it('未设置 TTL 的缓存应该永不过期', () => {
      cache.set('test-key', { data: 'test' })
      vi.advanceTimersByTime(999999)
      expect(cache.get('test-key')).toEqual({ data: 'test' })
    })
  })

  describe('LocalStorage 持久化', () => {
    it('应该将 persistent 缓存保存到 localStorage', () => {
      const testData = { id: 1, name: 'Test' }
      cache.set('persist-key', testData, { persistent: true })

      const stored = localStorageMock.store.get('edugenius_cache_persist-key')
      expect(stored).toBeDefined()
      expect(JSON.parse(stored!)).toEqual({
        data: testData,
        timestamp: expect.any(Number),
        ttl: undefined
      })
    })

    it('应该能够从 localStorage 恢复缓存', () => {
      const testData = { id: 1, name: 'Test' }
      cache.set('persist-key', testData, { persistent: true })

      // 清空内存缓存
      cache.clear()

      // 应该能从 localStorage 恢复
      expect(cache.get('persist-key')).toEqual(testData)
    })

    it('过期的 persistent 缓存应该被忽略', () => {
      const testData = { id: 1, name: 'Test' }
      cache.set('persist-key', testData, { persistent: true, ttl: 1000 })

      vi.advanceTimersByTime(1001)

      // 清空内存缓存
      cache.clear()

      // 过期的缓存应该无法恢复
      expect(cache.get('persist-key')).toBeNull()
    })
  })

  describe('工具函数', () => {
    it('generateCacheKey 应该生成正确的缓存键', () => {
      const key1 = generateCacheKey('documents', {})
      const key2 = generateCacheKey('documents', { sort: 'asc' })
      const key3 = generateCacheKey('documents', { sort: 'desc' })

      expect(key1).toBe('documents?')
      expect(key2).toBe('documents?sort:asc')
      expect(key3).toBe('documents?sort:desc')
    })

    it('generateCacheKey 应该对参数进行排序', () => {
      const key1 = generateCacheKey('test', { a: 1, b: 2 })
      const key2 = generateCacheKey('test', { b: 2, a: 1 })

      expect(key1).toBe(key2)
    })
  })

  describe('getOrSet 方法', () => {
    it('应该返回已有的缓存', async () => {
      const testData = { data: 'cached' }
      cache.set('test-key', testData)

      const fetcher = vi.fn().mockResolvedValue({ data: 'new' })
      const result = await cache.getOrSet('test-key', fetcher)

      expect(result).toEqual(testData)
      expect(fetcher).not.toHaveBeenCalled()
    })

    it('应该调用 fetcher 并缓存结果', async () => {
      const testData = { data: 'new' }
      const fetcher = vi.fn().mockResolvedValue(testData)

      const result = await cache.getOrSet('test-key', fetcher, {
        ttl: 5000,
        persistent: true
      })

      expect(result).toEqual(testData)
      expect(fetcher).toHaveBeenCalledTimes(1)
      expect(cache.get('test-key')).toEqual(testData)
    })
  })

  describe('has 方法', () => {
    it('应该正确判断缓存是否存在', () => {
      expect(cache.has('test-key')).toBe(false)

      cache.set('test-key', { data: 'test' })
      expect(cache.has('test-key')).toBe(true)

      cache.delete('test-key')
      expect(cache.has('test-key')).toBe(false)
    })

    it('过期的缓存应该返回 false', () => {
      cache.set('test-key', { data: 'test' }, { ttl: 1000 })
      expect(cache.has('test-key')).toBe(true)

      vi.advanceTimersByTime(1001)
      expect(cache.has('test-key')).toBe(false)
    })
  })

  describe('预定义配置', () => {
    it('CacheConfigs 应该包含正确的配置', () => {
      expect(CacheConfigs.documents).toEqual({
        ttl: 5 * 60 * 1000,
        persistent: true
      })

      expect(CacheConfigs.chapters).toEqual({
        ttl: 10 * 60 * 1000,
        persistent: true
      })

      expect(CacheConfigs.questions).toEqual({
        ttl: 5 * 60 * 1000,
        persistent: false
      })
    })
  })
})
