'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { submitSessionAnswer, completeQuizSession } from '@/lib/quiz-api';
import type { Question, CompleteSessionResponse } from '@/lib/quiz-api';

// Types
interface QuizProps {
  questions: Question[];
  sessionId: string;
  onComplete: (results: CompleteSessionResponse) => void;
  documentId?: number;
  chapterNumber?: number;
  userId?: number;
  token?: string;
  onCompetencyUpdate?: (competencyData: any) => void;
}

// 自定义比较函数，优化 Quiz 组件重渲染
function arePropsEqual(prevProps: QuizProps, nextProps: QuizProps) {
  return (
    prevProps.questions.length === nextProps.questions.length &&
    prevProps.questions.every((q, i) => q.id === nextProps.questions[i].id) &&
    prevProps.sessionId === nextProps.sessionId &&
    prevProps.documentId === nextProps.documentId &&
    prevProps.chapterNumber === nextProps.chapterNumber
  )
}

export default React.memo(function Quiz({
  questions,
  sessionId,
  onComplete,
  documentId,
  chapterNumber,
  userId,
  token,
  onCompetencyUpdate
}: QuizProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<string>('');
  const [showResult, setShowResult] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<{ isCorrect: boolean; message: string; explanation?: string } | null>(null);

  // 修复：每题独立计时，而不是整个测试共用一个开始时间
  const questionStartTimeRef = useRef<number>(Date.now());

  const currentQuestion = questions[currentIndex];
  const isLastQuestion = currentIndex === questions.length - 1;
  const progress = ((currentIndex + 1) / questions.length) * 100;

  // 当切换到新题目时，重置开始时间
  useEffect(() => {
    questionStartTimeRef.current = Date.now();
  }, [currentIndex]);

  // Handle answer selection
  const handleSelectAnswer = (answer: string) => {
    setSelectedAnswer(answer);
    setFeedback(null);
  };

  // Submit current answer
  const handleSubmitAnswer = async () => {
    if (!selectedAnswer || !sessionId) return;

    setIsSubmitting(true);

    // 计算本题用时（从开始显示当前题目到现在）
    const timeSpent = Math.floor((Date.now() - questionStartTimeRef.current) / 1000);

    try {
      // 使用 session API 提交答案
      const response = await submitSessionAnswer({
        sessionId: sessionId,
        questionId: currentQuestion.id,
        answer: selectedAnswer,
        timeSpent: timeSpent
      });

      setFeedback({
        isCorrect: response.is_correct,
        message: response.feedback,
        explanation: response.explanation
      });
    } catch (error) {
      console.error('Failed to submit answer:', error);
      // 显示错误提示
      setFeedback({
        isCorrect: false,
        message: '提交失败，请重试',
        explanation: error instanceof Error ? error.message : '网络错误'
      });
    }

    setIsSubmitting(false);
  };

  // Next question or complete quiz
  const handleNext = async () => {
    if (isLastQuestion) {
      // 完成测试，获取完整分析
      await handleCompleteQuiz();
    } else {
      setCurrentIndex(prev => prev + 1);
      setSelectedAnswer('');
      setFeedback(null);
    }
  };

  // Complete quiz and get full analysis
  const handleCompleteQuiz = async () => {
    if (!sessionId) return;

    setIsSubmitting(true);

    try {
      // 调用后端获取完整分析
      const results = await completeQuizSession(sessionId);

      // 触发能力数据更新
      if (onCompetencyUpdate && results.competency_analysis) {
        onCompetencyUpdate(results.competency_analysis);
      }

      // 传递完整结果给父组件
      onComplete(results);
    } catch (error) {
      console.error('Failed to complete quiz:', error);
      // 如果失败，仍然显示结果但提示错误
      alert('获取测试结果失败，请刷新页面重试');
    }

    setIsSubmitting(false);
  };

  if (questions.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500">暂无题目</p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto p-6">
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700">
            题目 {currentIndex + 1} / {questions.length}
          </span>
          <span className="text-sm text-gray-500">{Math.round(progress)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <motion.div
            className="bg-black h-2 rounded-full transition-all duration-300"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
      </div>

      {/* Question Card */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentIndex}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.3 }}
          className="bg-white border border-gray-200 rounded-xl p-8 shadow-sm"
        >
          {/* Question */}
          <div className="mb-6">
            <div className="flex items-start justify-between mb-4">
              <span className="inline-block px-3 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded-full">
                难度 {'★'.repeat(currentQuestion.difficulty)}
              </span>
              {currentQuestion.competency_dimension && (
                <span className="inline-block px-3 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded-full">
                  {currentQuestion.competency_dimension}
                </span>
              )}
            </div>
            <h2 className="text-xl font-semibold text-gray-900 leading-relaxed">
              {currentQuestion.question_text}
            </h2>
          </div>

          {/* Options */}
          {(currentQuestion.question_type === 'choice' || currentQuestion.question_type === 'conceptual') && currentQuestion.options && (
            <div className="space-y-3">
              {Object.entries(currentQuestion.options).map(([key, value]) => (
                <motion.button
                  key={key}
                  whileHover={{ scale: 1.01 }}
                  whileTap={{ scale: 0.99 }}
                  onClick={() => handleSelectAnswer(key)}
                  disabled={feedback !== null}
                  className={`w-full text-left p-4 border-2 rounded-lg transition-all duration-200 ${
                    selectedAnswer === key
                      ? 'border-black bg-gray-50'
                      : feedback !== null
                      ? 'border-gray-200 opacity-50 cursor-not-allowed'
                      : 'border-gray-200 hover:border-gray-400'
                  }`}
                >
                  <div className="flex items-center">
                    <span className="flex-shrink-0 w-8 h-8 flex items-center justify-center border-2 border-current rounded-full mr-3 font-medium">
                      {key}
                    </span>
                    <span className="text-gray-700">{value}</span>
                  </div>
                </motion.button>
              ))}
            </div>
          )}

          {/* Fill in the blank */}
          {currentQuestion.question_type === 'fill_blank' && (
            <div>
              <input
                type="text"
                value={selectedAnswer}
                onChange={(e) => handleSelectAnswer(e.target.value)}
                disabled={feedback !== null}
                placeholder="请输入答案..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-black focus:border-transparent outline-none transition-all disabled:opacity-50"
              />
            </div>
          )}

          {/* Feedback */}
          {feedback && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`mt-6 p-4 rounded-lg ${
                feedback.isCorrect ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
              }`}
            >
              <p className={`font-medium mb-2 ${feedback.isCorrect ? 'text-green-900' : 'text-red-900'}`}>
                {feedback.message}
              </p>
              {feedback.explanation && (
                <p className="text-sm text-gray-700">{feedback.explanation}</p>
              )}
            </motion.div>
          )}

          {/* Actions */}
          <div className="mt-6 flex justify-between">
            {feedback === null ? (
              <button
                onClick={handleSubmitAnswer}
                disabled={!selectedAnswer || isSubmitting}
                className="ml-auto px-6 py-3 bg-black text-white rounded-lg font-medium hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? '提交中...' : '提交答案'}
              </button>
            ) : (
              <button
                onClick={handleNext}
                disabled={isSubmitting}
                className="ml-auto px-6 py-3 bg-black text-white rounded-lg font-medium hover:bg-gray-800 transition-colors disabled:opacity-50"
              >
                {isSubmitting ? '处理中...' : isLastQuestion ? '查看结果' : '下一题'}
              </button>
            )}
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}, arePropsEqual)