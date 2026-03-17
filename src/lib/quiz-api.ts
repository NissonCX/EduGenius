/**
 * Quiz Session API 客户端
 *
 * 提供测试 session 相关的 API 调用功能
 */

import { fetchWithAuth } from './api-client'
import { getApiUrl } from './config'

// ============ 类型定义 ============

export interface Question {
  id: number
  question_type: string
  question_text: string
  options?: { [key: string]: string }
  correct_answer?: string
  explanation?: string
  difficulty: number
  competency_dimension?: string
}

export interface StartSessionParams {
  documentId: number
  chapterNumber: number
  subsectionNumber?: string
  questionCount?: number
  mode?: 'practice' | 'test'
}

export interface StartSessionResponse {
  session_id: string
  questions: Question[]
  total_questions: number
  estimated_time: number
  mode: string
  chapter_number: number
  subsection_number?: string
}

export interface SubmitAnswerParams {
  sessionId: string
  questionId: number
  answer: string
  timeSpent: number // 秒
}

export interface SubmitAnswerResponse {
  is_correct: boolean
  correct_answer: string
  explanation?: string
  feedback: string
  question_number: number
}

export interface CompetencyAnalysis {
  comprehension?: number | null
  logic?: number | null
  terminology?: number | null
  memory?: number | null
  application?: number | null
  stability?: number | null
}

export interface WeakPoint {
  dimension: string
  score: number
  name: string
}

export interface CompleteSessionResponse {
  score: number
  total: number
  correct: number
  passed: boolean
  competency_analysis: CompetencyAnalysis
  weak_points: WeakPoint[]
  recommendations: string[]
  mistake_ids: number[]
  time_spent_minutes: number
}

// ============ API 函数 ============

/**
 * 开始一个新的测试 session
 */
export async function startQuizSession(
  params: StartSessionParams
): Promise<StartSessionResponse> {
  const requestBody: Record<string, any> = {
    document_id: params.documentId,
    chapter_number: params.chapterNumber,
    question_count: params.questionCount ?? 10,
    mode: params.mode ?? 'practice'
  }

  if (params.subsectionNumber) {
    requestBody.subsection_number = params.subsectionNumber
  }

  const response = await fetchWithAuth(
    getApiUrl('/api/quiz/start-session'),
    {
      method: 'POST',
      body: JSON.stringify(requestBody)
    }
  )

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || '开始测试失败')
  }

  return response.json()
}

/**
 * 提交单题答案
 */
export async function submitSessionAnswer(
  params: SubmitAnswerParams
): Promise<SubmitAnswerResponse> {
  const response = await fetchWithAuth(
    getApiUrl(`/api/quiz/${params.sessionId}/submit-answer?question_id=${params.questionId}`),
    {
      method: 'POST',
      body: JSON.stringify({
        answer: params.answer,
        time_spent: params.timeSpent
      })
    }
  )

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || '提交答案失败')
  }

  return response.json()
}

/**
 * 完成测试，获取完整分析
 */
export async function completeQuizSession(
  sessionId: string
): Promise<CompleteSessionResponse> {
  const response = await fetchWithAuth(
    getApiUrl(`/api/quiz/${sessionId}/complete`),
    {
      method: 'POST'
    }
  )

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || '完成测试失败')
  }

  return response.json()
}

/**
 * 获取章节/小节题目列表
 */
export async function getChapterQuestions(
  documentId: number,
  chapterNumber: number,
  subsectionNumber?: string
): Promise<{ questions: Question[]; total: number }> {
  let url = `/api/quiz/questions/${documentId}/${chapterNumber}`
  if (subsectionNumber) {
    url += `?subsection_number=${encodeURIComponent(subsectionNumber)}`
  }

  const response = await fetchWithAuth(getApiUrl(url))

  if (!response.ok) {
    throw new Error('获取题目失败')
  }

  return response.json()
}

/**
 * AI 生成题目
 */
export async function generateQuestions(params: {
  documentId: number
  chapterNumber: number
  subsectionNumber?: string
  questionType?: string
  difficulty?: number
  count?: number
}): Promise<Question[]> {
  const requestBody: Record<string, any> = {
    document_id: params.documentId,
    chapter_number: params.chapterNumber,
    question_type: params.questionType ?? 'choice',
    difficulty: params.difficulty ?? 3,
    count: params.count ?? 5
  }

  if (params.subsectionNumber) {
    requestBody.subsection_number = params.subsectionNumber
  }

  const response = await fetchWithAuth(
    getApiUrl('/api/quiz/generate'),
    {
      method: 'POST',
      body: JSON.stringify(requestBody)
    }
  )

  if (!response.ok) {
    throw new Error('生成题目失败')
  }

  return response.json()
}