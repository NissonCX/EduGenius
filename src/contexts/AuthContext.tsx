'use client'

import { createContext, useContext, useState, useEffect, useCallback, useMemo, ReactNode } from 'react'
import { useRouter } from 'next/navigation'

interface User {
  id: number | null
  email: string | null
  username: string | null
  teachingStyle: number | null
  token?: string | null
}

interface AuthState {
  user: User
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
}

interface AuthContextType extends AuthState {
  login: (token: string, userId: number, email: string, username: string, teachingStyle: number) => void
  logout: () => void
  updateUser: (updates: Partial<User>) => void
  getAuthHeaders: (contentType?: boolean) => HeadersInit
  checkAuth: () => boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const INITIAL_USER: User = {
  id: null,
  email: null,
  username: null,
  teachingStyle: null,
  token: null
}

interface AuthProviderProps {
  children: ReactNode
}

/**
 * AuthProvider - 全局认证状态管理
 *
 * 使用 React Context 确保所有组件共享同一份认证状态
 * 解决登录后其他组件（如 Sidebar）不同步更新的问题
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const [authState, setAuthState] = useState<AuthState>({
    user: INITIAL_USER,
    token: null,
    isAuthenticated: false,
    isLoading: false  // 🔧 关键修复：初始状态不阻塞
  })

  const router = useRouter()

  // 从 localStorage 加载用户信息（组件挂载时执行一次）
  useEffect(() => {
    // 🔧 设置为加载中
    setAuthState(prev => ({ ...prev, isLoading: true }))

    const loadAuth = () => {
      try {
        const token = localStorage.getItem('token')
        const userId = localStorage.getItem('user_id')
        const email = localStorage.getItem('user_email')
        const username = localStorage.getItem('username')
        const teachingStyle = localStorage.getItem('teaching_style')

        const isAuthenticated = !!token && !!userId

        setAuthState({
          user: {
            id: userId ? parseInt(userId, 10) : null,
            email,
            username,
            teachingStyle: teachingStyle ? parseInt(teachingStyle, 10) : null,
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
    teachingStyle: number
  ) => {
    try {
      // Store individual keys (for backward compatibility)
      localStorage.setItem('token', token)
      localStorage.setItem('user_id', userId.toString())
      localStorage.setItem('user_email', email)
      localStorage.setItem('username', username)
      localStorage.setItem('teaching_style', teachingStyle.toString())

      // Also store complete user object (for easy retrieval)
      const userObj = {
        id: userId,
        email,
        username,
        teachingStyle
      }
      localStorage.setItem('user', JSON.stringify(userObj))

      setAuthState({
        user: { id: userId, email, username, teachingStyle, token },
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
      localStorage.removeItem('teaching_style')
      localStorage.removeItem('user')  // Also remove the complete user object

      setAuthState({
        user: INITIAL_USER,
        token: null,
        isAuthenticated: false,
        isLoading: false
      })

      // 登出后跳转到首页
      router.push('/')
    } catch (error) {
      console.error('登出失败:', error)
    }
  }, [router])

  // 更新用户信息
  const updateUser = useCallback((updates: Partial<User>) => {
    setAuthState(prev => {
      const newUser = { ...prev.user, ...updates }

      // 同步到 localStorage
      if (newUser.id !== null) {
        localStorage.setItem('user_id', newUser.id.toString())
      }
      if (newUser.teachingStyle !== null) {
        localStorage.setItem('teaching_style', newUser.teachingStyle.toString())
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
  const getAuthHeaders = useCallback((includeContentType: boolean = true) => {
    const headers: Record<string, string> = {}

    // 始终添加 Authorization 头（如果有 token）
    if (authState.token) {
      headers['Authorization'] = `Bearer ${authState.token}`
    }

    // 根据参数决定是否添加 Content-Type
    if (includeContentType) {
      headers['Content-Type'] = 'application/json'
    }

    return headers
  }, [authState.token])

  // 检查是否已认证
  const checkAuth = useCallback(() => {
    return authState.isAuthenticated && authState.user.id !== null
  }, [authState.isAuthenticated, authState.user.id])

  // 使用 useMemo 缓存 context value，避免不必要的重新渲染
  // 只在关键值改变时才重新创建对象
  const value = useMemo<AuthContextType>(() => ({
    user: authState.user,
    token: authState.token,
    isAuthenticated: authState.isAuthenticated,
    isLoading: authState.isLoading,
    login,
    logout,
    updateUser,
    getAuthHeaders,
    checkAuth
  }), [
    authState.user,
    authState.token,
    authState.isAuthenticated,
    authState.isLoading,
    login,
    logout,
    updateUser,
    getAuthHeaders,
    checkAuth
  ])

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

/**
 * useAuth - 认证管理 Hook
 *
 * 使用 Context 共享全局认证状态，确保登录后所有组件同步更新
 */
export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
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
