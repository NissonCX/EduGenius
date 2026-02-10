/**
 * Vitest 测试设置文件
 * 在所有测试运行前执行
 */

import { expect, afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

// 扩展 Vitest 的 expect，支持 jest-dom 匹配器
expect.extend(matchers)

// 每个测试后自动清理 React 组件
afterEach(() => {
  cleanup()
})

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

// Mock matchMedia（用于 Framer Motion 等库）
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => {}
  })
})

// Mock IntersectionObserver（用于懒加载组件）
class IntersectionObserverMock {
  observe() {}
  disconnect() {}
  unobserve() {}
}

Object.defineProperty(window, 'IntersectionObserver', {
  writable: true,
  configurable: true,
  value: IntersectionObserverMock
})

// Mock ResizeObserver
class ResizeObserverMock {
  observe() {}
  disconnect() {}
  unobserve() {}
}

Object.defineProperty(window, 'ResizeObserver', {
  writable: true,
  configurable: true,
  value: ResizeObserverMock
})
