'use client';

import React, { ReactNode } from 'react';
import { motion } from 'framer-motion';
import { RefreshCw, Download, MoreVertical } from 'lucide-react';

export interface ChartCardProps {
  title: string;
  description?: string;
  tooltip?: string;
  tooltipPosition?: 'top' | 'bottom' | 'left' | 'right';
  children: ReactNode;
  actions?: Array<{
    icon: ReactNode;
    label: string;
    onClick: () => void;
  }>;
  showRefresh?: boolean;
  onRefresh?: () => void;
  isRefreshing?: boolean;
  className?: string;
  headerClassName?: string;
  contentClassName?: string;
}

export function ChartCard({
  title,
  description,
  tooltip,
  tooltipPosition = 'top',
  children,
  actions,
  showRefresh = false,
  onRefresh,
  isRefreshing = false,
  className = '',
  headerClassName = '',
  contentClassName = ''
}: ChartCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={`bg-white border border-gray-200 rounded-2xl overflow-hidden ${className}`}
    >
      {/* 卡片头部 */}
      <div className={`px-6 py-4 border-b border-gray-100 ${headerClassName}`}>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
            {description && (
              <p className="text-sm text-gray-500 mt-1">{description}</p>
            )}
          </div>

          {/* 操作按钮组 */}
          <div className="flex items-center gap-2">
            {/* 刷新按钮 */}
            {showRefresh && onRefresh && (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={onRefresh}
                disabled={isRefreshing}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label="刷新"
              >
                <RefreshCw
                  className={`w-4 h-4 text-gray-600 ${isRefreshing ? 'animate-spin' : ''}`}
                />
              </motion.button>
            )}

            {/* 自定义操作按钮 */}
            {actions?.map((action, index) => (
              <motion.button
                key={index}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={action.onClick}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                aria-label={action.label}
              >
                {action.icon}
              </motion.button>
            ))}

            {/* 更多选项按钮 */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              aria-label="更多选项"
            >
              <MoreVertical className="w-4 h-4 text-gray-600" />
            </motion.button>
          </div>
        </div>
      </div>

      {/* 卡片内容 */}
      <div className={`p-6 ${contentClassName}`}>
        {children}
      </div>
    </motion.div>
  );
}
