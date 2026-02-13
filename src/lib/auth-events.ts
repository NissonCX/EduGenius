/**
 * 认证事件系统
 *
 * 解决问题：
 * - localStorage 变化不会触发 storage 事件（仅跨标签页触发）
 * - Token过期后需要通知所有组件更新UI状态
 *
 * 使用方式：
 * - dispatchAuthLogout() - 在任何地方触发登出事件
 * - onAuthLogout(callback) - 监听登出事件
 */

export const AUTH_LOGOUT_EVENT = 'auth-logout'

interface AuthLogoutDetail {
  reason: 'session_expired' | 'manual' | 'token_refresh_failed'
  timestamp: number
}

/**
 * 触发登出事件
 * 用于通知所有监听组件用户已登出
 */
export function dispatchAuthLogout(reason: 'session_expired' | 'manual' | 'token_refresh_failed' = 'manual') {
  if (typeof window === 'undefined') return

  const event = new CustomEvent<AuthLogoutDetail>(AUTH_LOGOUT_EVENT, {
    detail: {
      reason,
      timestamp: Date.now()
    }
  })

  window.dispatchEvent(event)
}

/**
 * 监听登出事件
 * @returns 清理函数
 */
export function onAuthLogout(callback: (detail: AuthLogoutDetail) => void) {
  if (typeof window === 'undefined') return () => {}

  const handler = (event: Event) => {
    const customEvent = event as CustomEvent<AuthLogoutDetail>
    callback(customEvent.detail)
  }

  window.addEventListener(AUTH_LOGOUT_EVENT, handler)

  // 返回清理函数
  return () => {
    window.removeEventListener(AUTH_LOGOUT_EVENT, handler)
  }
}

/**
 * 获取登出原因的友好提示文本
 */
export function getLogoutReasonMessage(reason: 'session_expired' | 'manual' | 'token_refresh_failed'): string {
  switch (reason) {
    case 'session_expired':
      return '登录已过期，请重新登录'
    case 'token_refresh_failed':
      return '登录状态失效，请重新登录'
    case 'manual':
      return '已退出登录'
    default:
      return '请重新登录'
  }
}
