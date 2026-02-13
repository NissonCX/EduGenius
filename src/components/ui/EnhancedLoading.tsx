'use client';

import React, { ReactNode, useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Clock, Loader2 } from 'lucide-react';

// Progress Steps Interface
export interface ProgressStep {
  icon: ReactNode;
  label: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
}

// Progress Stepper Component
interface ProgressStepperProps {
  steps: ProgressStep[];
  currentStep: number;
  className?: string;
}

export const ProgressStepper: React.FC<ProgressStepperProps> = ({
  steps,
  currentStep,
  className = ''
}) => {
  return (
    <div className={`space-y-3 ${className}`}>
      {steps.map((step, index) => {
        const isActive = index === currentStep;
        const isCompleted = step.status === 'completed';
        const isError = step.status === 'error';

        return (
          <motion.div
            key={index}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.2, delay: index * 0.05 }}
            className={`flex items-start gap-3 p-3 rounded-xl transition-all ${
              isActive ? 'bg-gray-50' : 'bg-transparent'
            }`}
          >
            {/* Icon Container */}
            <div
              className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center transition-all ${
                isCompleted
                  ? 'bg-green-50'
                  : isActive
                    ? 'bg-black'
                    : isError
                      ? 'bg-red-50'
                      : 'bg-gray-100'
              }`}
            >
              {isCompleted ? (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: 'spring', duration: 0.3 }}
                  className="text-green-600"
                >
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                </motion.div>
              ) : isActive ? (
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  className="text-white"
                >
                  <Loader2 className="w-5 h-5" />
                </motion.div>
              ) : (
                <div
                  className={`${
                    isError ? 'text-red-600' : 'text-gray-400'
                  } transition-colors`}
                >
                  {step.icon}
                </div>
              )}
            </div>

            {/* Label */}
            <div className="flex-1 min-w-0">
              <p
                className={`text-sm font-medium transition-colors ${
                  isActive || isCompleted
                    ? 'text-gray-900'
                    : 'text-gray-500'
                }`}
              >
                {step.label}
              </p>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
};

// Animated Loader Component
interface AnimatedLoaderProps {
  message: string;
  detail?: string;
  estimatedTime?: number; // seconds
  showCancel?: boolean;
  onCancel?: () => void;
}

export const AnimatedLoader: React.FC<AnimatedLoaderProps> = ({
  message,
  detail,
  estimatedTime,
  showCancel = false,
  onCancel
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.2 }}
      className="flex flex-col items-center justify-center p-8 bg-white rounded-2xl border border-gray-200"
    >
      {/* Animated Spinner */}
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
        className="mb-4"
      >
        <Loader2 className="w-12 h-12 text-black" />
      </motion.div>

      {/* Message */}
      <p className="text-lg font-semibold text-gray-900 mb-2">{message}</p>

      {/* Detail */}
      {detail && (
        <p className="text-sm text-gray-500 text-center mb-4">{detail}</p>
      )}

      {/* Estimated Time */}
      {estimatedTime && (
        <div className="flex items-center gap-2 text-sm text-gray-500 mb-4">
          <Clock className="w-4 h-4" />
          <span>预计需要 {estimatedTime} 秒</span>
        </div>
      )}

      {/* Cancel Button */}
      {showCancel && onCancel && (
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={onCancel}
          className="mt-2 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
        >
          取消
        </motion.button>
      )}
    </motion.div>
  );
};

// Time Estimate Component
interface TimeEstimateProps {
  elapsed: number; // seconds
  estimated?: number; // seconds
  variant?: 'short' | 'detailed';
}

export const TimeEstimate: React.FC<TimeEstimateProps> = ({
  elapsed,
  estimated,
  variant = 'detailed'
}) => {
  const formatTime = (seconds: number) => {
    if (seconds < 60) {
      return `${seconds}秒`;
    }
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return secs > 0 ? `${mins}分${secs}秒` : `${mins}分钟`;
  };

  const progress = estimated ? (elapsed / estimated) * 100 : 0;
  const isOverdue = estimated && elapsed > estimated;

  if (variant === 'short') {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Clock className="w-4 h-4" />
        <span>{formatTime(elapsed)}</span>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-500">已用时间</span>
        <span className="font-medium text-gray-900">{formatTime(elapsed)}</span>
      </div>

      {estimated && (
        <>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">预计时间</span>
            <span
              className={`font-medium ${
                isOverdue ? 'text-orange-600' : 'text-gray-900'
              }`}
            >
              {formatTime(estimated)}
            </span>
          </div>

          {/* Progress Bar */}
          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
            <motion.div
              className={`h-full rounded-full transition-colors ${
                isOverdue ? 'bg-orange-500' : 'bg-black'
              }`}
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(progress, 100)}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>

          {/* Remaining Time */}
          {!isOverdue && (
            <div className="text-xs text-gray-400 text-center">
              预计还需 {formatTime(estimated - elapsed)}
            </div>
          )}
        </>
      )}
    </div>
  );
};

// Cycling Message Component
interface CyclingMessageProps {
  messages: string[];
  interval?: number; // ms
  className?: string;
}

export const CyclingMessage: React.FC<CyclingMessageProps> = ({
  messages,
  interval = 2000,
  className = ''
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % messages.length);
    }, interval);

    return () => clearInterval(timer);
  }, [messages, interval]);

  return (
    <motion.div
      key={currentIndex}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.2 }}
      className={`text-sm text-gray-500 ${className}`}
    >
      {messages[currentIndex]}
    </motion.div>
  );
};

// Dots Loading Animation
interface DotsLoaderProps {
  size?: number;
  color?: string;
  className?: string;
}

export const DotsLoader: React.FC<DotsLoaderProps> = ({
  size = 8,
  color = '#9CA3AF',
  className = ''
}) => {
  return (
    <div className={`flex gap-1 ${className}`}>
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="rounded-full"
          style={{
            width: size,
            height: size,
            backgroundColor: color
          }}
          animate={{
            y: [0, -12, 0],
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
  );
};

// Pulse Ring Loader
interface PulseRingLoaderProps {
  size?: number;
  className?: string;
}

export const PulseRingLoader: React.FC<PulseRingLoaderProps> = ({
  size = 40,
  className = ''
}) => {
  return (
    <div className={`relative ${className}`} style={{ width: size, height: size }}>
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="absolute inset-0 rounded-full border-2 border-black"
          initial={{ scale: 0.5, opacity: 1 }}
          animate={{
            scale: [0.5, 1.5],
            opacity: [1, 0]
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            delay: i * 0.5,
            ease: 'easeOut'
          }}
        />
      ))}
    </div>
  );
};
