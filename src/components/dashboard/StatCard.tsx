'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { ArrowUp, ArrowDown, Minus } from 'lucide-react';

export interface StatCardProps {
  title: string;
  value: string | number;
  unit?: string;
  icon: React.ReactNode;
  trend?: {
    value: number; // percentage
    direction: 'up' | 'down' | 'neutral';
  };
  onClick?: () => void;
  className?: string;
  description?: string;
}

export function StatCard({
  title,
  value,
  unit,
  icon,
  trend,
  onClick,
  className = '',
  description
}: StatCardProps) {
  const cardContent = (
    <motion.div
      whileHover={{
        y: -4,
        boxShadow: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)'
      }}
      transition={{ duration: 0.25 }}
      className={`bg-white border border-gray-200 rounded-2xl p-6 transition-all ${onClick ? 'cursor-pointer' : ''} ${className}`}
      onClick={onClick}
    >
      {/* 头部：图标和标题 */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-gray-50 rounded-xl">
            {icon}
          </div>
          <div>
            <h3 className="text-sm font-medium text-gray-600">{title}</h3>
            {description && (
              <p className="text-xs text-gray-400 mt-0.5">{description}</p>
            )}
          </div>
        </div>
      </div>

      {/* 数值显示 */}
      <div className="flex items-baseline gap-2">
        <span className="text-3xl font-bold text-gray-900">
          {value}
        </span>
        {unit && (
          <span className="text-sm text-gray-500">{unit}</span>
        )}
      </div>

      {/* 趋势指示器 */}
      {trend && (
        <div className="flex items-center gap-2 mt-3">
          {trend.direction === 'up' ? (
            <div className="flex items-center gap-1 text-green-600">
              <ArrowUp className="w-4 h-4" />
              <span className="text-sm font-medium">+{trend.value}%</span>
            </div>
          ) : trend.direction === 'down' ? (
            <div className="flex items-center gap-1 text-red-600">
              <ArrowDown className="w-4 h-4" />
              <span className="text-sm font-medium">{trend.value}%</span>
            </div>
          ) : (
            <div className="flex items-center gap-1 text-gray-500">
              <Minus className="w-4 h-4" />
              <span className="text-sm font-medium">{trend.value}%</span>
            </div>
          )}
          <span className="text-xs text-gray-400">vs 上周</span>
        </div>
      )}
    </motion.div>
  );

  return cardContent;
}
