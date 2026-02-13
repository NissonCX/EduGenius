'use client';

/**
 * TypingIndicator - AI 正在思考/输入的动画指示器
 * 增强版：添加思考动画、计时器和上下文消息轮播
 */

import { motion } from 'framer-motion';
import { BrainCircuit, Clock } from 'lucide-react';
import { useState, useEffect } from 'react';
import { CyclingMessage } from '@/components/ui/EnhancedLoading';

interface ThinkingTimerProps {
  startTime: number;
}

function ThinkingTimer({ startTime }: ThinkingTimerProps) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);

    return () => clearInterval(timer);
  }, [startTime]);

  const formatTime = (seconds: number) => {
    if (seconds < 60) {
      return `${seconds}秒`;
    }
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return secs > 0 ? `${mins}分${secs}秒` : `${mins}分钟`;
  };

  return (
    <div className="flex items-center gap-1.5 text-xs text-gray-500">
      <Clock className="w-3.5 h-3.5" />
      <span>{formatTime(elapsed)}</span>
    </div>
  );
}

interface TypingIndicatorProps {
  startTime?: number;
  showTimer?: boolean;
}

export function TypingIndicator({
  startTime = Date.now(),
  showTimer = true
}: TypingIndicatorProps) {
  const thinkingMessages = [
    '正在分析你的问题...',
    '整理知识结构...',
    '准备详细回答...'
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex gap-3"
    >
      {/* AI 头像 - 带动画的脑图标 */}
      <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
        <motion.div
          animate={{
            scale: [1, 1.1, 1],
            rotate: [0, 5, -5, 0]
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'easeInOut'
          }}
        >
          <BrainCircuit className="w-5 h-5 text-gray-600" />
        </motion.div>
      </div>

      <div className="flex-1">
        {/* 思考消息气泡 */}
        <div className="bg-gray-50 rounded-2xl rounded-tl-sm p-4 border border-gray-100">
          {/* 打字动画点 */}
          <div className="flex items-center gap-1 mb-2">
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                className="w-2 h-2 rounded-full bg-gray-400"
                animate={{
                  y: [0, -8, 0],
                  opacity: [0.5, 1, 0.5]
                }}
                transition={{
                  duration: 0.6,
                  repeat: Infinity,
                  delay: i * 0.1,
                  ease: 'easeInOut'
                }}
              />
            ))}
          </div>

          {/* 轮播的上下文消息 */}
          <CyclingMessage
            messages={thinkingMessages}
            interval={2000}
            className="text-sm text-gray-600"
          />
        </div>

        {/* 计时器和状态 */}
        <div className="flex items-center gap-3 mt-2 ml-1">
          {showTimer && <ThinkingTimer startTime={startTime} />}
          <div className="flex items-center gap-1.5 text-xs text-gray-400">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span>思考中</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
