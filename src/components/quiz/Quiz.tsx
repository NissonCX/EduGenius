'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { getApiUrl } from '@/lib/config';

// Types
interface Question {
  id: number;
  question_type: string;
  question_text: string;
  options?: { [key: string]: string };
  correct_answer: string;
  explanation?: string;
  difficulty: number;
  competency_dimension?: string;
}

interface QuizProps {
  questions: Question[];
  onComplete: (results: QuizResults) => void;
  documentId?: number;
  chapterNumber?: number;
  userId?: number;
  token?: string;
  onCompetencyUpdate?: (competencyData: any) => void;
}

interface QuizResults {
  total: number;
  correct: number;
  score: number;
  answers: { questionId: number; userAnswer: string; isCorrect: boolean }[];
}

export default function Quiz({ questions, onComplete, documentId, chapterNumber, userId, token, onCompetencyUpdate }: QuizProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<string>('');
  const [userAnswers, setUserAnswers] = useState<{ questionId: number; userAnswer: string }[]>([]);
  const [showResult, setShowResult] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [startTime] = useState(Date.now());
  const [feedback, setFeedback] = useState<{ isCorrect: boolean; message: string; explanation?: string } | null>(null);

  const currentQuestion = questions[currentIndex];
  const isLastQuestion = currentIndex === questions.length - 1;
  const progress = ((currentIndex + 1) / questions.length) * 100;

  // Handle answer selection
  const handleSelectAnswer = (answer: string) => {
    setSelectedAnswer(answer);
    setFeedback(null);
  };

  // Submit current answer
  const handleSubmitAnswer = async () => {
    if (!selectedAnswer) return;

    setIsSubmitting(true);

    // Call API to submit answer
    try {
      if (token && userId) {
        const timeSpent = Math.floor((Date.now() - startTime) / 1000);
        const response = await fetch(getApiUrl('/api/quiz/submit'), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            user_id: userId,
            question_id: currentQuestion.id,
            user_answer: selectedAnswer,
            time_spent_seconds: timeSpent
          })
        });

        if (response.ok) {
          const data = await response.json();
          setFeedback({
            isCorrect: data.is_correct,
            message: data.feedback,
            explanation: data.explanation
          });
        } else {
          // Fallback to local validation if API fails
          const isCorrect = selectedAnswer.toUpperCase() === currentQuestion.correct_answer.toUpperCase();
          setFeedback({
            isCorrect,
            message: isCorrect ? '✅ 回答正确！' : `❌ 回答错误。正确答案是：${currentQuestion.correct_answer}`,
            explanation: currentQuestion.explanation
          });
        }
      } else {
        // No auth - use local validation only
        const isCorrect = selectedAnswer.toUpperCase() === currentQuestion.correct_answer.toUpperCase();
        setFeedback({
          isCorrect,
          message: isCorrect ? '✅ 回答正确！' : `❌ 回答错误。正确答案是：${currentQuestion.correct_answer}`,
          explanation: currentQuestion.explanation
        });
      }
    } catch (error) {
      console.error('Failed to submit answer:', error);
      // Fallback to local validation on error
      const isCorrect = selectedAnswer.toUpperCase() === currentQuestion.correct_answer.toUpperCase();
      setFeedback({
        isCorrect,
        message: isCorrect ? '✅ 回答正确！' : `❌ 回答错误。正确答案是：${currentQuestion.correct_answer}`,
        explanation: currentQuestion.explanation
      });
    }

    // Save answer
    setUserAnswers(prev => [
      ...prev,
      { questionId: currentQuestion.id, userAnswer: selectedAnswer }
    ]);

    setIsSubmitting(false);
  };

  // Next question
  const handleNext = () => {
    if (isLastQuestion) {
      // Quiz complete
      handleSubmitQuiz();
    } else {
      setCurrentIndex(prev => prev + 1);
      setSelectedAnswer('');
      setFeedback(null);
    }
  };

  // Submit entire quiz
  const handleSubmitQuiz = async () => {
    const correctCount = userAnswers.reduce((count, answer) => {
      const question = questions.find(q => q.id === answer.questionId);
      if (!question) return count;
      return count + (answer.userAnswer.toUpperCase() === question.correct_answer.toUpperCase() ? 1 : 0);
    }, 0);

    const results: QuizResults = {
      total: questions.length,
      correct: correctCount,
      score: (correctCount / questions.length) * 100,
      answers: userAnswers.map(answer => {
        const question = questions.find(q => q.id === answer.questionId);
        return {
          questionId: answer.questionId,
          userAnswer: answer.userAnswer,
          isCorrect: question ? answer.userAnswer.toUpperCase() === question.correct_answer.toUpperCase() : false
        };
      })
    };

    // 刷新能力数据
    if (userId && token && onCompetencyUpdate) {
      try {
        const response = await fetch(getApiUrl(`/api/users/${userId}/history`), {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.ok) {
          const data = await response.json();
          if (data.competency_scores) {
            onCompetencyUpdate(data.competency_scores);
          }
        }
      } catch (error) {
        console.error('Failed to refresh competency data:', error);
      }
    }

    onComplete(results);
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
          {currentQuestion.question_type === 'choice' && currentQuestion.options && (
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
                className="ml-auto px-6 py-3 bg-black text-white rounded-lg font-medium hover:bg-gray-800 transition-colors"
              >
                {isLastQuestion ? '查看结果' : '下一题'}
              </button>
            )}
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
