/**
 * 数据缓存工具
 * 提供内存缓存和 LocalStorage 持久化缓存
 */

interface CacheEntry<T> {
  data: T
  timestamp: number
  ttl?: number // 毫秒
}

interface CacheConfig {
  ttl?: number // 默认过期时间（毫秒）
  persistent?: boolean // 是否持久化到 LocalStorage
}

class DataCache {
  private memoryCache = new Map<string, CacheEntry<any>>()
  private localStoragePrefix = 'edugenius_cache_'

  /**
   * 生成缓存键
   */
  private getStorageKey(key: string): string {
    return `${this.localStoragePrefix}${key}`
  }

  /**
   * 设置缓存
   */
  set<T>(key: string, data: T, config: CacheConfig = {}): void {
    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      ttl: config.ttl
    }

    // 内存缓存
    this.memoryCache.set(key, entry)

    // 持久化缓存
    if (config.persistent) {
      try {
        const storageKey = this.getStorageKey(key)
        localStorage.setItem(storageKey, JSON.stringify(entry))
      } catch (error) {
        console.warn('[Cache] Failed to save to localStorage:', error)
      }
    }
  }

  /**
   * 获取缓存
   */
  get<T>(key: string): T | null {
    // 先尝试从内存获取
    const memoryEntry = this.memoryCache.get(key)
    if (memoryEntry && this.isValid(memoryEntry)) {
      return memoryEntry.data as T
    }

    // 尝试从 LocalStorage 获取
    const storageKey = this.getStorageKey(key)
    const stored = localStorage.getItem(storageKey)
    if (stored) {
      try {
        const entry: CacheEntry<T> = JSON.parse(stored)
        if (this.isValid(entry)) {
          // 回填到内存缓存
          this.memoryCache.set(key, entry)
          return entry.data
        } else {
          // 过期则删除
          localStorage.removeItem(storageKey)
        }
      } catch (error) {
        console.warn('[Cache] Failed to parse from localStorage:', error)
        localStorage.removeItem(storageKey)
      }
    }

    return null
  }

  /**
   * 检查缓存是否有效
   */
  private isValid(entry: CacheEntry<any>): boolean {
    if (!entry.ttl) return true
    return Date.now() - entry.timestamp < entry.ttl
  }

  /**
   * 删除缓存
   */
  delete(key: string): void {
    this.memoryCache.delete(key)
    const storageKey = this.getStorageKey(key)
    localStorage.removeItem(storageKey)
  }

  /**
   * 清空所有缓存
   */
  clear(): void {
    this.memoryCache.clear()

    // 清空 LocalStorage 中的缓存
    const keys = Object.keys(localStorage)
    keys.forEach(key => {
      if (key.startsWith(this.localStoragePrefix)) {
        localStorage.removeItem(key)
      }
    })
  }

  /**
   * 检查缓存是否存在且有效
   */
  has(key: string): boolean {
    return this.get(key) !== null
  }

  /**
   * 获取或设置缓存（类似 Redis 的 get_or_set）
   */
  getOrSet<T>(
    key: string,
    fetcher: () => Promise<T>,
    config: CacheConfig = {}
  ): Promise<T> {
    const cached = this.get<T>(key)
    if (cached !== null) {
      return Promise.resolve(cached)
    }

    return fetcher().then(data => {
      this.set(key, data, config)
      return data
    })
  }
}

// 单例实例
export const cache = new DataCache()

// 预定义的缓存配置
export const CacheConfigs = {
  // 文档列表：5分钟
  documents: { ttl: 5 * 60 * 1000, persistent: true },

  // 章节列表：10分钟
  chapters: { ttl: 10 * 60 * 1000, persistent: true },

  // 小节列表：10分钟
  subsections: { ttl: 10 * 60 * 1000, persistent: true },

  // 章节问题：5分钟
  questions: { ttl: 5 * 60 * 1000, persistent: false },

  // 学习历史：3分钟
  history: { ttl: 3 * 60 * 1000, persistent: false },

  // 用户信息：30分钟
  user: { ttl: 30 * 60 * 1000, persistent: true },

  // 能力评估：15分钟
  competency: { ttl: 15 * 60 * 1000, persistent: true },
}

/**
 * 生成缓存键的辅助函数
 */
export function generateCacheKey(prefix: string, params: Record<string, any>): string {
  const sortedParams = Object.keys(params)
    .sort()
    .map(key => `${key}:${params[key]}`)
    .join('|')
  return `${prefix}?${sortedParams}`
}
