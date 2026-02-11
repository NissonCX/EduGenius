'use client';

/**
 * GitHub风格的学习日历组件
 * 类似 GitHub contribution graph，展示学习记录
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { getApiUrl, getAuthHeadersSimple } from '@/lib/config';

interface ActivityDay {
  date: string;
  count: number;
  level: number; // 0-4，用于计算颜色深度
}

interface ActivityMonth {
  year: number;
  month: number;
  days: ActivityDay[];
}

interface StudyCalendarProps {
  userId?: number;
  documentId?: number;
}

export function StudyCalendar({ userId, documentId }: StudyCalendarProps) {
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  const [activityData, setActivityData] = useState<Record<number, ActivityMonth>>({});
  const [loading, setLoading] = useState(true);
  const [totalDays, setTotalDays] = useState({ count: 0, minutes: 0 });

  // 获取颜色类名（类似GitHub）
  const getColorClass = (level: number) => {
    const colors = [
      'bg-gray-100', // level 0 - 无活动
      'bg-green-100', // level 1 - 轻度
      'bg-green-200', // level 2 - 中度
      'bg-green-300', // level 3 - 较强
      'bg-green-400', // level 4 - 强烈
    ];
    return colors[level] || colors[0];
  };

  // 获取某月的天数和第一天星期
  const getMonthInfo = (year: number, month: number) => {
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    return { firstDay, daysInMonth };
  };

  // 加载学习活动数据
  useEffect(() => {
    if (!userId) {
      setLoading(false);
      return;
    }

    const loadActivityData = async () => {
      try {
        // 获取用户的学习活动历史
        const response = await fetch(
          getApiUrl(`/api/users/${userId}/activity-calendar?year=${currentYear}`),
          {
            headers: getAuthHeadersSimple()
          }
        );

        if (response.ok) {
          const data = await response.json();
          setActivityData(data.months || {});

          // 计算总统计
          const allDays = Object.values(data.months || {}).flatMap(m => m.days);
          const totalCount = allDays.reduce((sum, day) => sum + day.count, 0);
          const totalMinutes = allDays.reduce((sum, day) => sum + (day.level * 5), 0); // 估算：level * 5分钟

          setTotalDays({ count: totalCount, minutes: totalMinutes });
        } else {
          console.error('Failed to load activity data');
        }
      } catch (error) {
        console.error('Error loading activity:', error);
      } finally {
        setLoading(false);
      }
    };

    loadActivityData();
  }, [userId, currentYear]);

  // 渲染月份
  const renderMonth = (monthIndex: number) => {
    const month = activityData[monthIndex];
    if (!month) return null;

    const { firstDay, daysInMonth } = getMonthInfo(currentYear, monthIndex);
    const monthNames = ['一月', '二月', '三月', '四月', '五月', '六月',
                       '七月', '八月', '九月', '十月', '十一月', '十二月'];

    return (
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <h3 className="text-sm font-semibold text-gray-700">{monthNames[monthIndex]}</h3>
          <span className="text-xs text-gray-500">
            {month.days.reduce((sum, day) => sum + day.count, 0)} 次学习
          </span>
        </div>
        <div className="grid grid-cols-7 gap-1">
          {/* 星期标题 */}
          {['日', '一', '二', '三', '四', '五', '六'].map((day) => (
            <div key={day} className="text-xs text-gray-500 text-center py-1">
              {day}
            </div>
          ))}

          {/* 空白填充前面的天数 */}
          {Array.from({ length: firstDay }).map((_, i) => (
            <div key={`empty-${i}`} className="aspect-square" />
          ))}

          {/* 实际天数 */}
          {month.days.map((day) => (
            <div
              key={day.date}
              className="aspect-square"
              title={`${day.date}: ${day.count}次学习, 强度${day.level}`}
            >
              <div className={`w-full h-full rounded-sm ${getColorClass(day.level)} transition-all hover:opacity-80 hover:ring-1 hover:ring-green-500`} />
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-300 border-t-black mx-auto" />
          <p className="mt-4 text-sm text-gray-600">加载学习记录中...</p>
        </div>
      </div>
    );
  }

  if (!userId) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <p className="text-sm text-gray-500 text-center">请先登录查看学习记录</p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white border border-gray-200 rounded-xl p-6"
    >
      {/* 头部：年份切换和统计 */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900">
          学习日历 · {currentYear}
        </h2>
        <div className="flex items-center gap-4">
          {/* 年份切换 */}
          <button
            onClick={() => setCurrentYear(currentYear - 1)}
            disabled={currentYear <= 2020}
            className="px-3 py-1 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            ← 上一年
          </button>
          <button
            onClick={() => setCurrentYear(currentYear + 1)}
            disabled={currentYear >= new Date().getFullYear() + 1}
            className="px-3 py-1 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            下一年 →
          </button>
        </div>
      </div>

      {/* 统计信息 */}
      {totalDays.count > 0 && (
        <div className="grid grid-cols-3 gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
          <div>
            <p className="text-xs text-gray-500 mb-1">学习天数</p>
            <p className="text-2xl font-bold text-gray-900">{totalDays.count}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">学习次数</p>
            <p className="text-2xl font-bold text-gray-900">{totalDays.count}次</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">总时长</p>
            <p className="text-2xl font-bold text-gray-900">{Math.round(totalDays.minutes / 60)}小时</p>
          </div>
        </div>
      )}

      {/* 图例 */}
      <div className="flex items-center gap-4 mb-6 text-xs">
        <span className="text-gray-500">少</span>
        <div className="flex gap-1">
          <div className="w-4 h-4 rounded-sm bg-green-100" />
          <div className="w-4 h-4 rounded-sm bg-green-200" />
          <div className="w-4 h-4 rounded-sm bg-green-300" />
          <div className="w-4 h-4 rounded-sm bg-green-400" />
        </div>
        <span className="text-gray-500">多</span>
      </div>

      {/* 12个月的日历 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {Array.from({ length: 12 }, (_, i) => renderMonth(i))}
      </div>

      {/* 提示信息 */}
      {totalDays.count === 0 && (
        <div className="text-center py-8">
          <p className="text-sm text-gray-500">
            还没有学习记录，开始学习后将在这里看到你的足迹 📚
          </p>
        </div>
      )}
    </motion.div>
  );
}
