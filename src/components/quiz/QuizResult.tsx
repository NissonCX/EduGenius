'use client';

import React from 'react';
import { motion } from 'framer-motion';

interface QuizResultProps {
  score: number;
  correctCount: number;
  totalCount: number;
  competencyScores?: { [key: string]: number };
  recommendations?: string[];
  onRetry?: () => void;
  onNextChapter?: () => void;
  onViewMistakes?: () => void;
  passed?: boolean;
}

const competencyNames: { [key: string]: string } = {
  comprehension: '理解能力',
  logic: '逻辑推理',
  terminology: '术语掌握',
  memory: '记忆能力',
  application: '应用能力',
  stability: '稳定性'
};

export default function QuizResult({
  score,
  correctCount,
  totalCount,
  competencyScores,
  recommendations = [],
  onRetry,
  onNextChapter,
  onViewMistakes,
  passed = false
}: QuizResultProps) {
  const percentage = Math.round(score);

  return (
    <div className="max-w-3xl mx-auto p-6">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
        className="bg-white border border-gray-200 rounded-xl p-8 shadow-sm"
      >
        {/* Score Circle */}
        <div className="flex flex-col items-center mb-8">
          <div className={`relative w-40 h-40 rounded-full flex items-center justify-center ${
            passed ? 'bg-green-50' : 'bg-red-50'
          }`}>
            <svg className="absolute inset-0 w-full h-full transform -rotate-90">
              <circle
                cx="80"
                cy="80"
                r="70"
                fill="none"
                stroke={passed ? '#22c55e' : '#ef4444'}
                strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray={`${2 * Math.PI * 70}`}
                strokeDashoffset={`${2 * Math.PI * 70 * (1 - percentage / 100)}`}
              />
            </svg>
            <div className="text-center">
              <div className={`text-4xl font-bold ${passed ? 'text-green-600' : 'text-red-600'}`}>
                {percentage}%
              </div>
              <div className="text-sm text-gray-600 mt-1">
                {correctCount}/{totalCount} 正确
              </div>
            </div>
          </div>

          <h2 className={`text-2xl font-bold mt-6 ${passed ? 'text-green-700' : 'text-red-700'}`}>
            {passed ? '🎉 恭喜通过！' : '💪 继续努力！'}
          </h2>
          <p className="text-gray-600 mt-2">
            {passed
              ? '你已经掌握了本章的主要内容'
              : '建议复习本章内容后再进行测试'}
          </p>
        </div>

        {/* Competency Scores */}
        {competencyScores && (
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">能力维度分析</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {Object.entries(competencyScores)
                .filter(([_, score]) => typeof score === 'number' && score > 0)
                .map(([dimension, score]) => {
                  const percentage = Math.round(score * 100);
                  return (
                    <div key={dimension} className="bg-gray-50 rounded-lg p-4">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium text-gray-700">
                          {competencyNames[dimension] || dimension}
                        </span>
                        <span className="text-sm font-bold text-gray-900">{percentage}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full transition-all ${
                            percentage >= 60 ? 'bg-green-500' : 'bg-orange-500'
                          }`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>
        )}

        {/* Recommendations */}
        {recommendations.length > 0 && (
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">学习建议</h3>
            <div className="space-y-2">
              {recommendations.map((rec, index) => (
                <div key={index} className="flex items-start">
                  <span className="text-blue-500 mr-2">💡</span>
                  <span className="text-gray-700">{rec}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3">
          {!passed && onRetry && (
            <button
              onClick={onRetry}
              className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
            >
              重新测试
            </button>
          )}
          {passed && onNextChapter && (
            <button
              onClick={onNextChapter}
              className="flex-1 px-6 py-3 bg-black text-white rounded-lg font-medium hover:bg-gray-800 transition-colors"
            >
              进入下一章
            </button>
          )}
          {onViewMistakes && (
            <button
              onClick={onViewMistakes}
              className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
            >
              查看错题
            </button>
          )}
        </div>
      </motion.div>
    </div>
  );
}
