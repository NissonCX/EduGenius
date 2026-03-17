'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { ArrowLeft, BookOpen, Brain, CheckCircle, Sparkles } from 'lucide-react';
import { Quiz, QuizResult } from '@/components/quiz';
import { safeFetch } from '@/lib/errors';
import { useAuth } from '@/contexts/AuthContext';
import { getApiUrl } from '@/lib/config';
import { Skeleton, ChatListSkeleton } from '@/components/ui/Skeleton';
import {
  ProgressStepper,
  ProgressStep,
  TimeEstimate,
  AnimatedLoader
} from '@/components/ui/EnhancedLoading';

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

function QuizPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, token, getAuthHeaders } = useAuth();
  
  // 使用新的参数名称
  const docId = searchParams.get('doc');
  const chapterId = searchParams.get('chapter');
  const subsectionId = searchParams.get('subsection'); // 新增：小节参数
  const mode = searchParams.get('mode') || 'practice'; // 'practice' or 'test'

  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [quizResults, setQuizResults] = useState<QuizResults | null>(null);
  const [documentTitle, setDocumentTitle] = useState('');
  const [chapterTitle, setChapterTitle] = useState('');
  const [subsectionTitle, setSubsectionTitle] = useState(''); // 新增：小节标题
  const [generationStartTime, setGenerationStartTime] = useState<number>(0);
  const [currentGenerationStep, setCurrentGenerationStep] = useState(0);
  const [generationSteps, setGenerationSteps] = useState<ProgressStep[]>([
    { icon: <BookOpen className="w-5 h-5" />, label: '分析章节内容', status: 'pending' },
    { icon: <Brain className="w-5 h-5" />, label: 'AI 生成题目', status: 'pending' },
    { icon: <CheckCircle className="w-5 h-5" />, label: '验证答案准确性', status: 'pending' },
    { icon: <Sparkles className="w-5 h-5" />, label: '优化题目表述', status: 'pending' }
  ]);

  useEffect(() => {
    if (docId && chapterId) {
      loadChapterInfo();
      loadQuestions();
    } else {
      setError('缺少必需参数：doc 或 chapter');
      setLoading(false);
    }
  }, [docId, chapterId, subsectionId]); // 添加 subsectionId 依赖

  const loadChapterInfo = async () => {
    try {
      const response = await fetch(getApiUrl(`/api/documents/${docId}/chapters`), {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const data = await response.json();
        setDocumentTitle(data.document_title);
        const chapter = data.chapters.find((c: any) => c.chapter_number === parseInt(chapterId!));
        if (chapter) {
          setChapterTitle(chapter.chapter_title);
        }
      }
    } catch (err) {
      console.error('加载章节信息失败:', err);
    }
  };

  const loadQuestions = async () => {
    try {
      setLoading(true);
      setError(null);

      // 构建API URL，如果有小节参数则添加
      let apiUrl = `/api/quiz/questions/${docId}/${chapterId}`;
      if (subsectionId) {
        apiUrl += `?subsection_number=${encodeURIComponent(subsectionId)}`;
      }

      // Get questions from API
      const response = await fetch(
        getApiUrl(apiUrl),
        { headers: getAuthHeaders() }
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
      setGenerating(true);
      setGenerationStartTime(Date.now());

      const requestBody: any = {
        document_id: parseInt(docId!),
        chapter_number: parseInt(chapterId!),
        question_type: 'choice',
        difficulty: 3,
        count: 5
      };

      // 如果有小节参数，添加到请求中
      if (subsectionId) {
        requestBody.subsection_number = subsectionId;
      }

      // 模拟步骤进度
      const updateStep = (stepIndex: number, status: ProgressStep['status']) => {
        setGenerationSteps(prev => {
          const newSteps = [...prev];
          newSteps[stepIndex].status = status;
          return newSteps;
        });
        setCurrentGenerationStep(stepIndex);
      };

      // 步骤 1: 分析章节内容
      updateStep(0, 'processing');
      await new Promise(resolve => setTimeout(resolve, 800));
      updateStep(0, 'completed');

      // 步骤 2: AI 生成题目
      updateStep(1, 'processing');
      await new Promise(resolve => setTimeout(resolve, 1200));

      const response = await fetch(getApiUrl('/api/quiz/generate'), {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error('生成题目失败');
      }

      updateStep(1, 'completed');

      // 步骤 3: 验证答案
      updateStep(2, 'processing');
      await new Promise(resolve => setTimeout(resolve, 600));
      updateStep(2, 'completed');

      // 步骤 4: 优化题目
      updateStep(3, 'processing');
      const data = await response.json();
      await new Promise(resolve => setTimeout(resolve, 400));
      updateStep(3, 'completed');

      setQuestions(data);
    } catch (err) {
      console.error('Error generating questions:', err);
      setError(err instanceof Error ? err.message : '生成题目失败');
      // 标记当前步骤为错误
      setGenerationSteps(prev => {
        const newSteps = [...prev];
        newSteps[currentGenerationStep].status = 'error';
        return newSteps;
      });
    } finally {
      setGenerating(false);
    }
  };

  const handleQuizComplete = (results: QuizResults) => {
    setQuizResults(results);
    setShowResult(true);
  };

  const handleCompetencyUpdate = (competencyData: any) => {
    // 触发全局事件通知 Dashboard 刷新能力数据
    console.log('Competency data updated:', competencyData);
    window.dispatchEvent(new CustomEvent('quiz-completed', {
      detail: { competencyData, timestamp: Date.now(), documentId: docId, chapterId }
    }));
  };

  const handleRetry = () => {
    setShowResult(false);
    setQuizResults(null);
    loadQuestions();
  };

  const handleNextChapter = () => {
    const nextChapter = parseInt(chapterId!) + 1;
    router.push(`/study?doc=${docId}&chapter=${nextChapter}`);
  };

  const handleViewMistakes = () => {
    router.push('/mistakes');
  };

  const handleBackToChapters = () => {
    router.push(`/study?doc=${docId}`);
  };

  if (loading || generating) {
    const elapsedSeconds = generationStartTime
      ? Math.floor((Date.now() - generationStartTime) / 1000)
      : 0;

    return (
      <div className="min-h-screen bg-white p-8">
        <div className="max-w-3xl mx-auto">
          {/* 标题骨架 */}
          <div className="mb-8">
            <Skeleton className="h-8 w-48 mb-2" />
            <Skeleton className="h-4 w-64" />
          </div>

          {/* 生成进度指示器 */}
          {generating ? (
            <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                AI 正在生成题目...
              </h3>
              <p className="text-sm text-gray-500 mb-6">
                根据章节内容智能生成测试题目，请稍候
              </p>

              {/* 进度步骤 */}
              <div className="mb-6">
                <ProgressStepper
                  steps={generationSteps}
                  currentStep={currentGenerationStep}
                />
              </div>

              {/* 时间估算 */}
              <div className="border-t border-gray-100 pt-4">
                <TimeEstimate
                  elapsed={elapsedSeconds}
                  estimated={45}
                  variant="detailed"
                />
              </div>
            </div>
          ) : (
            /* 题目骨架 */
            <ChatListSkeleton count={3} />
          )}
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
    <div className="min-h-screen bg-white">
      {/* 顶部导航栏 */}
      <div className="border-b border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={handleBackToChapters}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-gray-600" />
              </button>
              <div>
                <h1 className="font-semibold text-lg text-black">
                  {chapterTitle || `第 ${chapterId} 章`} - 章节测试
                </h1>
                <p className="text-sm text-gray-500">{documentTitle}</p>
              </div>
            </div>
            <div className="text-sm text-gray-600">
              共 {questions.length} 道题
            </div>
          </div>
        </div>
      </div>

      {/* 测试内容 */}
      <div className="max-w-4xl mx-auto px-6 py-8">
        <Quiz
          questions={questions}
          onComplete={handleQuizComplete}
          documentId={parseInt(docId!)}
          chapterNumber={parseInt(chapterId!)}
          userId={user?.id ?? undefined}
          token={token ?? undefined}
          onCompetencyUpdate={handleCompetencyUpdate}
        />
      </div>
    </div>
  );
}

export default function QuizPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-black mx-auto mb-4"></div>
          <p className="text-gray-600">加载中...</p>
        </div>
      </div>
    }>
      <QuizPageContent />
    </Suspense>
  );
}
