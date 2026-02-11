'use client';

/**
 * 学习日历组件 - 符合项目设计风格
 * 简洁的数据可视化，类似学习热力图
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Calendar, ChevronLeft, ChevronRight, Flame, TrendingUp } from 'lucide-react';
import { getApiUrl, getAuthHeadersSimple } from '@/lib/config';

interface DayData {
  date: string;
  count: number;
  minutes: number;
}

interface StudyCalendarProps {
  userId?: number;
  documentId?: number;
}

export function StudyCalendar({ userId, documentId }: StudyCalendarProps) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [activityData, setActivityData] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [totalStats, setTotalStats] = useState({ days: 0, hours: 0 });

  // 获取月份名称
  const getMonthName = (month: number) => {
    const months = ['一月', '二月', '三月', '四月', '五月', '六月',
                     '七月', '八月', '九月', '十月', '十一月', '十二月'];
    return months[month - 1];
  };

  // 获取当月日历
  const getCalendarDays = (year: number, month: number) => {
    const firstDay = new Date(year, month - 1, 1).getDay();
    const daysInMonth = new Date(year, month, 0).getDate();
    const days = [];

    // 填充前面的空白
    for (let i = 0; i < firstDay; i++) {
      days.push(null);
    }

    // 填充实际日期
    for (let i = 1; i <= daysInMonth; i++) {
      days.push(i);
    }

    return days;
  };

  // 加载活动数据
  useEffect(() => {
    if (!userId) {
      setLoading(false);
      return;
    }

    const loadActivity = async () => {
      try {
        const year = currentDate.getFullYear();
        const response = await fetch(
          getApiUrl(`/api/users/${userId}/activity-calendar?year=${year}`),
          { headers: getAuthHeadersSimple() }
        );

        if (response.ok) {
          const data = await response.json();

          // 转换为简单的日期->活动强度映射
          const activityMap: Record<string, number> = {};
          if (data.months) {
            data.months.forEach((monthData: any) => {
              if (monthData.days) {
                monthData.days.forEach((day: any) => {
                  if (day.level > 0) {
                    activityMap[day.date] = day.level;
                  }
                });
              }
            });
          }

          setActivityData(activityMap);

          // 计算总统计
          const allDays = Object.values(activityMap);
          const activeDays = allDays.filter(v => v > 0).length;
          const totalMinutes = Object.values(activityMap).reduce((sum: number, level: number) => {
            // 估算：level * 10分钟
            return sum + (level * 10);
          }, 0);

          setTotalStats({
            days: activeDays,
            hours: Math.round(totalMinutes / 60)
          });
        }
      } catch (error) {
        console.error('Failed to load activity:', error);
      } finally {
        setLoading(false);
      }
    };

    loadActivity();
  }, [userId, currentDate.getFullYear()]);

  // 获取颜色类（简化版本，符合项目风格）
  const getColorClass = (level: number) => {
    const colors: Record<number, string> = {
      0: 'bg-gray-50',
      1: 'bg-emerald-100',
      2: 'bg-emerald-200',
      3: 'bg-emerald-400',
      4: 'bg-emerald-600',
    };
    return colors[level] || colors[0];
  };

  // 切换月份
  const changeMonth = (delta: number) => {
    const newDate = new Date(currentDate);
    newDate.setMonth(newDate.getMonth() + delta);
    setCurrentDate(newDate);
  };

  // 切换年份
  const changeYear = (delta: number) => {
    const newDate = new Date(currentDate);
    newDate.setFullYear(newDate.getFullYear() + delta);
    setCurrentDate(newDate);
  };

  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-10 w-10 border-2 border-gray-300 border-t-black mx-auto" />
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

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth() + 1;
  const calendarDays = getCalendarDays(year, month);
  const monthName = getMonthName(month);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white border border-gray-200 rounded-xl p-6"
    >
      {/* 头部：年份切换和统计 */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold text-gray-900">
          {year}年 {monthName}
        </h3>

        <div className="flex items-center gap-2">
          {/* 年份切换 */}
          <button
            onClick={() => changeYear(-1)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            disabled={year <= 2020}
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <button
            onClick={() => changeYear(1)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            disabled={year >= new Date().getFullYear() + 1}
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* 统计卡片 */}
      {totalStats.days > 0 && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
            <div className="flex items-center gap-2 mb-2">
              <Flame className="w-5 h-5 text-orange-500" />
              <div>
                <p className="text-xs text-gray-500 mb-1">学习天数</p>
                <p className="text-2xl font-bold text-gray-900">{totalStats.days}</p>
              </div>
            </div>
          </div>

          <div className="bg-emerald-50 rounded-xl p-4 border border-emerald-200">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-5 h-5 text-emerald-600" />
              <div>
                <p className="text-xs text-gray-500 mb-1">总时长</p>
                <p className="text-2xl font-bold text-gray-900">{totalStats.hours}h</p>
              </div>
            </div>
          </div>

          <div className="bg-blue-50 rounded-xl p-4 border border-blue-200">
            <div className="flex items-center gap-2 mb-2">
              <Calendar className="w-5 h-5 text-blue-600" />
              <div>
                <p className="text-xs text-gray-500 mb-1">活跃度</p>
                <p className="text-2xl font-bold text-gray-900">
                  {totalStats.days > 0
                    ? Math.round((totalStats.days / 365) * 100)
                    : 0}%
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 图例 */}
      <div className="flex items-center gap-4 mb-4 text-sm">
        <span className="text-gray-500">学习强度：</span>
        {[
          { level: 1, label: '轻度', color: 'bg-emerald-100' },
          { level: 2, label: '中度', color: 'bg-emerald-300' },
          { level: 3, label: '较强', color: 'bg-emerald-500' },
          { level: 4, label: '强烈', color: 'bg-emerald-700' },
        ].map((item) => (
          <div key={item.level} className="flex items-center gap-2">
            <div className={`w-4 h-4 rounded-sm ${item.color}`} />
            <span className="text-gray-600">{item.label}</span>
          </div>
        ))}
      </div>

      {/* 日历网格 */}
      <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
        <div className="grid grid-cols-7 gap-1 mb-2">
          {/* 星期标题 */}
          {['日', '一', '二', '三', '四', '五', '六'].map((day) => (
            <div key={day} className="text-center py-2">
              <span className="text-xs font-medium text-gray-500">{day}</span>
            </div>
          ))}

          {/* 日历日期 */}
          {calendarDays.map((day, index) => {
            if (day === null) {
              return <div key={`empty-${index}`} className="aspect-square" />;
            }

            const dateString = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const activityLevel = activityData[dateString] || 0;

            return (
              <div
                key={dateString}
                className={`aspect-square rounded-sm transition-all hover:opacity-80 ${getColorClass(activityLevel)}`}
                title={`${year}-${month}-${day}`}
              >
                <span className="text-sm font-medium text-gray-700">
                  {day}
                </span>
              </div>
            );
          })}
        </div>

        {/* 无数据提示 */}
        {totalStats.days === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">
              还没有学习记录，开始学习后将在这里看到你的足迹 📚
            </p>
          </div>
        )}
      </div>

      {/* 快速切换到当月 */}
      <div className="mt-4 flex justify-center">
        <button
          onClick={() => {
            const now = new Date();
            setCurrentDate(now);
          }}
          className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors text-sm"
        >
          回到今天
        </button>
      </div>
    </motion.div>
  );
}
