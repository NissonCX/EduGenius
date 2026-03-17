'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { ArrowLeft, BookOpen, Brain, CheckCircle, Sparkles } from 'lucide-react';
import { Quiz } from '@/components/quiz';
import QuizResult from '@/components/quiz/QuizResult';
import { useAuth } from '@/contexts/AuthContext';
import { getApiUrl } from '@/lib/config';
import { Skeleton, ChatListSkeleton } from '@/components/ui/Skeleton';
import {
  ProgressStepper,
  ProgressStep,
  TimeEstimate,
} from '@/components/ui/EnhancedLoading';
import {
  startQuizSession,
  generateQuestions,
  type Question,
  type CompleteSessionResponse,
  type StartSessionResponse
} from '@/lib/quiz-api';

interface ProgressStepData {
  icon: React.ReactNode;
  label: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
}

function QuizPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, token, getAuthHeaders } = useAuth();

  // URL 参数
  const docId = searchParams.get('doc');
  const chapterId = searchParams.get('chapter');
  const subsectionId = searchParams.get('subsection'); // 小节参数
  const mode = (searchParams.get('mode') as 'practice' | 'test') || 'practice';

  const [questions, setQuestions] = useState<Question[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [quizResults, setQuizResults] = useState<CompleteSessionResponse | null>(null);
  const [documentTitle, setDocumentTitle] = useState('');
  const [chapterTitle, setChapterTitle] = useState('');
  const [generationStartTime, setGenerationStartTime] = useState<number>(0);
  const [currentGenerationStep, setCurrentGenerationStep] = useState(0);
  const [generationSteps, setGenerationSteps] = useState<ProgressStepData[]>([
    { icon: <BookOpen className="w-5 h-5" />, label: '分析章节内容', status: 'pending' },
    { icon: <Brain className="w-5 h-5" />, label: 'AI 生成题目', status: 'pending' },
    { icon: <CheckCircle className="w-5 h-5" />, label: '验证答案准确性', status: 'pending' },
    { icon: <Sparkles className="w-5 h-5" />, label: '优化题目表述', status: 'pending' }
  ]);

  useEffect(() => {
    if (docId && chapterId) {
      initializeQuiz();
    } else {
      setError('缺少必需参数：doc 或 chapter');
      setLoading(false);
    }
  }, [docId, chapterId, subsectionId]);

  const initializeQuiz = async () => {
    try {
      setLoading(true);
      setError(null);

      // 1. 加载章节信息
      await loadChapterInfo();

      // 2. 尝试开始测试 session
      try {
        const sessionResponse = await startQuizSession({
          documentId: parseInt(docId!),
          chapterNumber: parseInt(chapterId!),
          subsectionNumber: subsectionId || undefined,
          questionCount: 10,
          mode: mode
        });

        setSessionId(sessionResponse.session_id);
        setQuestions(sessionResponse.questions);
      } catch (sessionError) {
        // 如果 session 失败（可能是没有题目），尝试生成题目
        console.log('Session start failed, trying to generate questions:', sessionError);
        await generateAndStartSession();
      }
    } catch (err) {
      console.error('Error initializing quiz:', err);
      setError(err instanceof Error ? err.message : '初始化测试失败');
    } finally {
      setLoading(false);
    }
  };

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

  const generateAndStartSession = async () => {
    try {
      setGenerating(true);
      setGenerationStartTime(Date.now());

      // 模拟步骤进度
      const updateStep = (stepIndex: number, status: ProgressStepData['status']) => {
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

      const generatedQuestions = await generateQuestions({
        documentId: parseInt(docId!),
        chapterNumber: parseInt(chapterId!),
        subsectionNumber: subsectionId || undefined,
        questionType: 'choice',
        difficulty: 3,
        count: 5
      });

      updateStep(1, 'completed');

      // 步骤 3: 验证答案
      updateStep(2, 'processing');
      await new Promise(resolve => setTimeout(resolve, 600));
      updateStep(2, 'completed');

      // 步骤 4: 优化题目
      updateStep(3, 'processing');
      await new Promise(resolve => setTimeout(resolve, 400));
      updateStep(3, 'completed');

      // 生成成功后，重新开始 session
      const sessionResponse = await startQuizSession({
        documentId: parseInt(docId!),
        chapterNumber: parseInt(chapterId!),
        subsectionNumber: subsectionId || undefined,
        questionCount: generatedQuestions.length,
        mode: mode
      });

      setSessionId(sessionResponse.session_id);
      setQuestions(sessionResponse.questions);
    } catch (err) {
      console.error('Error generating questions:', err);
      setError(err instanceof Error ? err.message : '生成题目失败');
      // 标记当前步骤为错误
      setGenerationSteps(prev => {
        const newSteps = [...prev];
        if (newSteps[currentGenerationStep]) {
          newSteps[currentGenerationStep].status = 'error';
        }
        return newSteps;
      });
    } finally {
      setGenerating(false);
    }
  };

  const handleQuizComplete = (results: CompleteSessionResponse) => {
    setQuizResults(results);
    setShowResult(true);

    // 触发全局事件通知 Dashboard 刷新能力数据
    window.dispatchEvent(new CustomEvent('quiz-completed', {
      detail: {
        competencyData: results.competency_analysis,
        timestamp: Date.now(),
        documentId: docId,
        chapterId
      }
    }));
  };

  const handleCompetencyUpdate = (competencyData: any) => {
    console.log('Competency data updated:', competencyData);
  };

  const handleRetry = () => {
    setShowResult(false);
    setQuizResults(null);
    setSessionId(null);
    setQuestions([]);
    initializeQuiz();
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
                  steps={generationSteps as ProgressStep[]}
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
    // 将 competency_analysis 转换为 QuizResult 组件期望的格式
    const competencyScores: { [key: string]: number } = {};
    if (quizResults.competency_analysis) {
      for (const [key, value] of Object.entries(quizResults.competency_analysis)) {
        if (value !== null) {
          // 转换为 0-1 的比例
          competencyScores[key] = value / 100;
        }
      }
    }

    return (
      <div className="min-h-screen bg-white">
        {/* 顶部导航栏 */}
        <div className="border-b border-gray-200 bg-white">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center gap-4">
              <button
                onClick={handleBackToChapters}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-gray-600" />
              </button>
              <div>
                <h1 className="font-semibold text-lg text-black">
                  {chapterTitle || `第 ${chapterId} 章`} - 测试结果
                </h1>
                <p className="text-sm text-gray-500">{documentTitle}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="max-w-4xl mx-auto px-6 py-8">
          <QuizResult
            score={quizResults.score}
            correctCount={quizResults.correct}
            totalCount={quizResults.total}
            competencyScores={competencyScores}
            recommendations={quizResults.recommendations}
            passed={quizResults.passed}
            onRetry={!quizResults.passed ? handleRetry : undefined}
            onNextChapter={quizResults.passed ? handleNextChapter : undefined}
            onViewMistakes={quizResults.mistake_ids.length > 0 ? handleViewMistakes : undefined}
          />
        </div>
      </div>
    );
  }

  // 检查是否有有效的 session
  if (!sessionId || questions.length === 0) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="text-6xl mb-4">📝</div>
          <p className="text-gray-700 mb-4">暂无可用题目</p>
          <button
            onClick={handleBackToChapters}
            className="px-6 py-3 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors"
          >
            返回章节
          </button>
        </div>
      </div>
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
          sessionId={sessionId}
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