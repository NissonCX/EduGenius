'use client'

import React, { Component, ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import { AlertCircle, RefreshCw, Home } from 'lucide-react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

/**
 * ErrorBoundary - 捕获组件树中的错误
 *
 * 捕获子组件中的 JavaScript 错误，
 * 显示友好的错误界面而不是白屏
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // 记录错误到控制台
    console.error('ErrorBoundary 捕获到错误:', error, errorInfo)

    // 这里可以添加错误日志服务（如 Sentry）
    // logErrorToService(error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      // 使用自定义 fallback 或默认错误界面
      if (this.props.fallback) {
        return this.props.fallback
      }

      return <DefaultErrorUI error={this.state.error} onReset={this.handleReset} />
    }

    return this.props.children
  }
}

/**
 * 默认错误界面
 */
function DefaultErrorUI({ error, onReset }: { error: Error | null; onReset: () => void }) {
  const router = useRouter()

  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        {/* 错误图标 */}
        <div className="flex justify-center mb-6">
          <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center">
            <AlertCircle className="w-8 h-8 text-red-500" />
          </div>
        </div>

        {/* 错误标题 */}
        <h1 className="text-2xl font-semibold text-black mb-2">
          出错了
        </h1>
        <p className="text-gray-600 mb-8">
          抱歉，应用遇到了意外错误。请尝试刷新页面或返回首页。
        </p>

        {/* 错误详情（开发环境） */}
        {process.env.NODE_ENV === 'development' && error && (
          <div className="mb-8 p-4 bg-gray-50 rounded-lg text-left">
            <p className="text-sm font-medium text-gray-700 mb-2">错误详情：</p>
            <p className="text-xs text-gray-500 font-mono break-all">{error.message}</p>
          </div>
        )}

        {/* 操作按钮 */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            onClick={() => window.location.reload()}
            className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            刷新页面
          </button>
          <button
            onClick={() => router.push('/')}
            className="inline-flex items-center justify-center gap-2 px-6 py-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Home className="w-4 h-4" />
            返回首页
          </button>
        </div>
      </div>
    </div>
  )
}

/**
 * useErrorHandler Hook
 *
 * 在函数组件中手动触发错误边界
 */
export function useErrorHandler() {
  return (error: Error) => {
    throw error
  }
}
