'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Quiz, QuizResult } from '@/components/quiz';
import { safeFetch } from '@/lib/api';

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

interface QuizResults {
  total: number;
  correct: number;
  score: number;
  answers: { questionId: number; userAnswer: string; isCorrect: boolean }[];
}

export default function QuizPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const documentId = searchParams.get('documentId');
  const chapterNumber = searchParams.get('chapterNumber');
  const mode = searchParams.get('mode') || 'practice'; // 'practice' or 'test'

  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [quizResults, setQuizResults] = useState<QuizResults | null>(null);

  useEffect(() => {
    if (documentId && chapterNumber) {
      loadQuestions();
    } else {
      setError('缺少必需参数：documentId 或 chapterNumber');
      setLoading(false);
    }
  }, [documentId, chapterNumber]);

  const loadQuestions = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get questions from API
      const response = await safeFetch(
        `http://localhost:8000/api/quiz/questions/${documentId}/${chapterNumber}`
      );

      if (!response.ok) {
        throw new Error('获取题目失败');
      }

      const data = await response.json();

      if (data.questions.length === 0) {
        // Generate sample questions if none exist
        await generateSampleQuestions();
      } else {
        setQuestions(data.questions);
      }
    } catch (err) {
      console.error('Error loading questions:', err);
      setError(err instanceof Error ? err.message : '加载题目失败');
    } finally {
      setLoading(false);
    }
  };

  const generateSampleQuestions = async () => {
    try {
      const response = await safeFetch('http://localhost:8000/api/quiz/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_id: parseInt(documentId!),
          chapter_number: parseInt(chapterNumber!),
          question_type: 'choice',
          difficulty: 3,
          count: 5
        })
      });

      if (!response.ok) {
        throw new Error('生成题目失败');
      }

      const data = await response.json();
      setQuestions(data);
    } catch (err) {
      console.error('Error generating questions:', err);
      setError(err instanceof Error ? err.message : '生成题目失败');
    }
  };

  const handleQuizComplete = (results: QuizResults) => {
    setQuizResults(results);
    setShowResult(true);
  };

  const handleRetry = () => {
    setShowResult(false);
    setQuizResults(null);
    loadQuestions();
  };

  const handleNextChapter = () => {
    const nextChapter = parseInt(chapterNumber!) + 1;
    router.push(`/study?documentId=${documentId}&chapter=${nextChapter}`);
  };

  const handleViewMistakes = () => {
    router.push('/mistakes');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-black mx-auto mb-4"></div>
          <p className="text-gray-600">加载题目中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <p className="text-gray-700 mb-4">{error}</p>
          <button
            onClick={() => router.back()}
            className="px-6 py-3 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors"
          >
            返回
          </button>
        </div>
      </div>
    );
  }

  if (showResult && quizResults) {
    const passed = quizResults.score >= 60;

    return (
      <QuizResult
        score={quizResults.score}
        correctCount={quizResults.correct}
        totalCount={quizResults.total}
        passed={passed}
        recommendations={
          passed
            ? ['🎉 恭喜通过测试！可以进入下一章节学习。']
            : ['📚 建议复习本章内容后再进行测试。']
        }
        onRetry={!passed ? handleRetry : undefined}
        onNextChapter={passed ? handleNextChapter : undefined}
        onViewMistakes={handleViewMistakes}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto">
        <div className="mb-6">
          <button
            onClick={() => router.back()}
            className="text-gray-600 hover:text-gray-900 transition-colors"
          >
            ← 返回
          </button>
        </div>

        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {mode === 'test' ? '章节测试' : '练习模式'}
        </h1>
        <p className="text-gray-600 mb-8">
          第 {chapterNumber} 章 · 共 {questions.length} 道题
        </p>

        <Quiz
          questions={questions}
          onComplete={handleQuizComplete}
          documentId={parseInt(documentId!)}
          chapterNumber={parseInt(chapterNumber!)}
        />
      </div>
    </div>
  );
}
