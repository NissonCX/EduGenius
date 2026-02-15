'use client'

import { useEffect } from 'react'
import { useToast } from './Toast'
import { onAuthLogout, getLogoutReasonMessage } from '@/lib/auth-events'

/**
 * 认证事件监听器
 * 监听全局认证登出事件并显示 Toast 提示
 */
export function AuthEventListener() {
  const { showError } = useToast()

  useEffect(() => {
    const cleanup = onAuthLogout((detail) => {
      const message = getLogoutReasonMessage(detail.reason)
      showError(message, 3000)
      console.log(`[Auth] 登出事件: ${detail.reason}`)
    })

    return cleanup
  }, [showError])

  return null
}
