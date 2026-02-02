'use client'

/**
 * Skeleton - 骨架屏组件
 *
 * 在内容加载时显示占位符，提升用户体验
 *
 * 使用方法:
 * ```tsx
 * <Skeleton className="h-4 w-32" />
 * <CardSkeleton />
 * <DocumentListSkeleton />
 * ```
 */

import { cn } from '@/lib/utils'

export function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('animate-pulse rounded-md bg-gray-200', className)}
      {...props}
    />
  )
}

/**
 * 卡片骨架屏 - 用于文档卡片等
 */
export function CardSkeleton() {
  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-6">
      {/* 标题骨架 */}
      <Skeleton className="h-6 w-3/4 mb-4" />

      {/* 内容骨架 */}
      <div className="space-y-3">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-5/6" />
        <Skeleton className="h-4 w-4/6" />
      </div>

      {/* 底部信息骨架 */}
      <div className="mt-6 flex items-center justify-between">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-8 w-20 rounded-lg" />
      </div>
    </div>
  )
}

/**
 * 文档列表骨架屏
 */
export function DocumentListSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {Array.from({ length: count }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  )
}

/**
 * 章节列表骨架屏
 */
export function ChapterListSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <ChapterItemSkeleton key={i} />
      ))}
    </div>
  )
}

/**
 * 章节项骨架屏
 */
export function ChapterItemSkeleton() {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <div className="flex items-center gap-4">
        {/* 图标 */}
        <Skeleton className="w-10 h-10 rounded-lg" />

        {/* 标题和信息 */}
        <div className="flex-1 space-y-2">
          <Skeleton className="h-5 w-48" />
          <Skeleton className="h-4 w-32" />
        </div>

        {/* 状态 */}
        <Skeleton className="h-6 w-16 rounded-full" />
      </div>
    </div>
  )
}

/**
 * 消息骨架屏 - 用于聊天界面
 */
export function MessageSkeleton() {
  return (
    <div className="flex gap-4 px-4 py-6">
      {/* 头像 */}
      <Skeleton className="w-9 h-9 rounded-full flex-shrink-0" />

      {/* 消息内容 */}
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-20" />
        <div className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
          <Skeleton className="h-4 w-4/6" />
        </div>
      </div>
    </div>
  )
}

/**
 * 聊天列表骨架屏
 */
export function ChatListSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-6">
      {Array.from({ length: count }).map((_, i) => (
        <MessageSkeleton key={i} />
      ))}
    </div>
  )
}

/**
 * 进度条骨架屏
 */
export function ProgressBarSkeleton() {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-4 w-16" />
      </div>
      <Skeleton className="h-2 w-full rounded-full" />
    </div>
  )
}

/**
 * 统计卡片骨架屏
 */
export function StatsCardSkeleton() {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      {/* 图标 */}
      <Skeleton className="w-12 h-12 rounded-lg mb-4" />

      {/* 数值 */}
      <Skeleton className="h-8 w-20 mb-2" />

      {/* 标签 */}
      <Skeleton className="h-4 w-24" />
    </div>
  )
}

/**
 * 仪表板骨架屏
 */
export function DashboardSkeleton() {
  return (
    <div className="space-y-8">
      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatsCardSkeleton />
        <StatsCardSkeleton />
        <StatsCardSkeleton />
      </div>

      {/* 进度卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <Skeleton className="h-6 w-32" />
          <ProgressBarSkeleton />
          <ProgressBarSkeleton />
          <ProgressBarSkeleton />
        </div>
        <div className="space-y-4">
          <Skeleton className="h-6 w-32" />
          <ProgressBarSkeleton />
          <ProgressBarSkeleton />
        </div>
      </div>
    </div>
  )
}

/**
 * 表格骨架屏
 */
export function TableSkeleton({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      {/* 表头 */}
      <div className="grid gap-4 p-4 border-b border-gray-200" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}>
        {Array.from({ length: cols }).map((_, i) => (
          <Skeleton key={i} className="h-4" />
        ))}
      </div>

      {/* 表体 */}
      <div className="divide-y divide-gray-200">
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div key={rowIndex} className="grid gap-4 p-4" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}>
            {Array.from({ length: cols }).map((_, colIndex) => (
              <Skeleton key={colIndex} className="h-4" />
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
