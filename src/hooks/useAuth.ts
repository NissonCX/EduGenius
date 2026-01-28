'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'

interface User {
  id: number | null
  email: string | null
  username: string | null
  cognitiveLevel: number | null
  token?: string | null
}

interface AuthState {
  user: User
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
}

const INITIAL_USER: User = {
  id: null,
  email: null,
  username: null,
  cognitiveLevel: null,
  token: null
}

/**
 * useAuth - 认证管理 Hook
 *
 * 提供统一的认证状态管理和操作方法
 * - 从 localStorage 读取用户信息
 * - 提供 login、logout、isAuthenticated 等方法
 * - 自动同步 localStorage 变化
 */
export function useAuth() {
  const [authState, setAuthState] = useState<AuthState>({
    user: INITIAL_USER,
    token: null,
    isAuthenticated: false,
    isLoading: true
  })

  // 从 localStorage 加载用户信息
  useEffect(() => {
    const loadAuth = () => {
      try {
        const token = localStorage.getItem('token')
        const userId = localStorage.getItem('user_id')
        const email = localStorage.getItem('user_email')
        const username = localStorage.getItem('username')
        const cognitiveLevel = localStorage.getItem('cognitive_level')

        const isAuthenticated = !!token && !!userId

        setAuthState({
          user: {
            id: userId ? parseInt(userId, 10) : null,
            email,
            username,
            cognitiveLevel: cognitiveLevel ? parseInt(cognitiveLevel, 10) : null,
            token: token
          },
          token,
          isAuthenticated,
          isLoading: false
        })
      } catch (error) {
        console.error('加载认证信息失败:', error)
        setAuthState({
          user: INITIAL_USER,
          token: null,
          isAuthenticated: false,
          isLoading: false
        })
      }
    }

    loadAuth()

    // 监听 storage 事件（多标签页同步）
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'token' || e.key === 'user_id') {
        loadAuth()
      }
    }

    window.addEventListener('storage', handleStorageChange)
    return () => window.removeEventListener('storage', handleStorageChange)
  }, [])

  // 登录
  const login = useCallback((
    token: string,
    userId: number,
    email: string,
    username: string,
    cognitiveLevel: number
  ) => {
    try {
      localStorage.setItem('token', token)
      localStorage.setItem('user_id', userId.toString())
      localStorage.setItem('user_email', email)
      localStorage.setItem('username', username)
      localStorage.setItem('cognitive_level', cognitiveLevel.toString())

      setAuthState({
        user: { id: userId, email, username, cognitiveLevel, token },
        token,
        isAuthenticated: true,
        isLoading: false
      })
    } catch (error) {
      console.error('登录失败:', error)
      throw error
    }
  }, [])

  // 登出
  const logout = useCallback(() => {
    try {
      localStorage.removeItem('token')
      localStorage.removeItem('user_id')
      localStorage.removeItem('user_email')
      localStorage.removeItem('username')
      localStorage.removeItem('cognitive_level')

      setAuthState({
        user: INITIAL_USER,
        token: null,
        isAuthenticated: false,
        isLoading: false
      })
    } catch (error) {
      console.error('登出失败:', error)
    }
  }, [])

  // 更新用户信息
  const updateUser = useCallback((updates: Partial<User>) => {
    setAuthState(prev => {
      const newUser = { ...prev.user, ...updates }

      // 同步到 localStorage
      if (newUser.id !== null) {
        localStorage.setItem('user_id', newUser.id.toString())
      }
      if (newUser.cognitiveLevel !== null) {
        localStorage.setItem('cognitive_level', newUser.cognitiveLevel.toString())
      }
      if (newUser.username !== null) {
        localStorage.setItem('username', newUser.username)
      }

      return {
        ...prev,
        user: newUser
      }
    })
  }, [])

  // 获取认证请求头
  const getAuthHeaders = useCallback(() => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json'
    }

    if (authState.token) {
      headers['Authorization'] = `Bearer ${authState.token}`
    }

    return headers
  }, [authState.token])

  // 检查是否已认证
  const checkAuth = useCallback(() => {
    return authState.isAuthenticated && authState.user.id !== null
  }, [authState.isAuthenticated, authState.user.id])

  return {
    // 状态
    ...authState,

    // 方法
    login,
    logout,
    updateUser,
    getAuthHeaders,
    checkAuth
  }
}

/**
 * useRequireAuth - 需要认证的 Hook
 *
 * 如果用户未登录，自动跳转到登录页
 */
export function useRequireAuth() {
  const auth = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!auth.isLoading && !auth.isAuthenticated) {
      router.push('/login')
    }
  }, [auth.isLoading, auth.isAuthenticated, router])

  return auth
}

// Next.js useRouter import（仅在服务端使用时需要）
function useRouter() {
  // 简化实现，实际应该从 next/navigation 导入
  return { push: (path: string) => { window.location.href = path } }
}
