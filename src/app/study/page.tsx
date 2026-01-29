'use client'

/**
 * /study - 学习页面
 * 
 * 流程：
 * 1. 没有 doc 参数 -> 显示文档选择界面
 * 2. 有 doc 但没有 chapter -> 显示章节选择界面
 * 3. 有 doc 和 chapter -> 显示学习对话界面
 */

import { useState, useEffect, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { BookOpen, ChevronRight, Lock, CheckCircle2, Loader2, ArrowLeft, Settings, MessageSquare } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { getApiUrl } from '@/lib/config'
import { StudyChat } from '@/components/chat/StudyChat'
import Link from 'next/link'

interface Document {
  id: number
  title: string
  filename: string
  total_chapters: number
  processing_status: string
}

interface Chapter {
  chapter_number: number
  chapter_title: string
  status: string
  completion_percentage: number
  is_locked: boolean
  lock_reason: string | null
  status_icon: string
  status_text: string
  subsections?: Subsection[]
  subsection_count?: number
}

interface Subsection {
  subsection_number: string
  subsection_title: string
  page_number?: number
  completion_percentage: number
  time_spent_minutes: number
}

function StudyPageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { user, isAuthenticated, getAuthHeaders } = useAuth()

  const docId = searchParams.get('doc')
  const chapterId = searchParams.get('chapter')
  const subsectionId = searchParams.get('subsection')  // 新增小节参数

  const [documents, setDocuments] = useState<Document[]>([])
  const [chapters, setChapters] = useState<Chapter[]>([])
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null)
  const [selectedChapter, setSelectedChapter] = useState<Chapter | null>(null)
  const [loading, setLoading] = useState(true)
  const [teachingStyle, setTeachingStyle] = useState(user?.teachingStyle || 3)
  const [expandedChapter, setExpandedChapter] = useState<number | null>(null)  // 控制章节展开

  // 加载文档列表
  useEffect(() => {
    // 只在确定未认证时跳转
    if (isAuthenticated === false) {
      router.push('/login')
      return
    }

    // 正在加载中或已认证
    if (!docId && isAuthenticated) {
      loadDocuments()
    }
  }, [isAuthenticated, docId])

  // 加载章节列表
  useEffect(() => {
    if (docId && !chapterId && isAuthenticated) {
      loadChapters(parseInt(docId))
    }
  }, [docId, chapterId, isAuthenticated])

  // 加载选中的章节
  useEffect(() => {
    if (docId && chapterId && isAuthenticated) {
      const chapterNum = parseInt(chapterId)
      if (!isNaN(chapterNum)) {
        loadSelectedChapter(parseInt(docId), chapterNum)
      }
    }
  }, [docId, chapterId, isAuthenticated])

  // 同步用户的教学风格
  useEffect(() => {
    if (user?.teachingStyle) {
      setTeachingStyle(user.teachingStyle)
    }
  }, [user?.teachingStyle])

  const loadDocuments = async () => {
    setLoading(true)
    try {
      const response = await fetch(getApiUrl('/api/documents/list'), {
        headers: getAuthHeaders()
      })

      if (response.ok) {
        const data = await response.json()
        setDocuments(data.documents || [])
      }
    } catch (err) {
      console.error('加载文档失败:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadChapters = async (documentId: number) => {
    setLoading(true)
    try {
      const response = await fetch(getApiUrl(`/api/documents/${documentId}/chapters`), {
        headers: getAuthHeaders()
      })

      if (response.ok) {
        const data = await response.json()
        setSelectedDoc({
          id: data.document_id,
          title: data.document_title,
          filename: data.document_title,
          total_chapters: data.total_chapters,
          processing_status: 'completed'
        })
        setChapters(data.chapters || [])
      }
    } catch (err) {
      console.error('加载章节失败:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadSelectedChapter = async (documentId: number, chapterNumber: number) => {
    setLoading(true)
    try {
      const response = await fetch(getApiUrl(`/api/documents/${documentId}/chapters`), {
        headers: getAuthHeaders()
      })

      if (response.ok) {
        const data = await response.json()
        setSelectedDoc({
          id: data.document_id,
          title: data.document_title,
          filename: data.document_title,
          total_chapters: data.total_chapters,
          processing_status: 'completed'
        })
        
        const chapter = data.chapters.find((c: Chapter) => c.chapter_number === chapterNumber)
        if (chapter) {
          setSelectedChapter(chapter)
        }
      }
    } catch (err) {
      console.error('加载章节失败:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleStyleChange = (style: number) => {
    setTeachingStyle(style)
  }

  // 1. 文档选择界面
  if (!docId) {
    return (
      <div className="min-h-screen bg-white">
        <div className="max-w-6xl mx-auto px-6 py-12">
          {/* 标题 */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-black mb-2">选择学习教材</h1>
            <p className="text-gray-600">从您上传的教材中选择一本开始学习</p>
          </div>

          {/* 文档列表 */}
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
            </div>
          ) : documents.length === 0 ? (
            <div className="text-center py-20">
              <BookOpen className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-600 mb-6">还没有上传任何教材</p>
              <Link
                href="/documents"
                className="inline-block px-6 py-3 bg-black text-white rounded-xl hover:bg-gray-800 transition-colors"
              >
                上传教材
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {documents.map((doc) => (
                <motion.button
                  key={doc.id}
                  onClick={() => router.push(`/study?doc=${doc.id}`)}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  whileHover={{ y: -4 }}
                  className="p-6 bg-white border-2 border-gray-200 rounded-2xl hover:border-black transition-all text-left group"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="p-3 bg-black text-white rounded-xl group-hover:scale-110 transition-transform">
                      <BookOpen className="w-6 h-6" />
                    </div>
                    <div className="text-sm text-gray-500">
                      {doc.total_chapters} 章节
                    </div>
                  </div>

                  <h3 className="font-semibold text-lg text-black mb-2 line-clamp-2">
                    {doc.title}
                  </h3>

                  <div className="flex items-center text-sm text-gray-600 group-hover:text-black transition-colors">
                    <span>开始学习</span>
                    <ChevronRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
                  </div>
                </motion.button>
              ))}
            </div>
          )}
        </div>
      </div>
    )
  }

  // 2. 章节选择界面
  if (docId && !chapterId) {
    return (
      <div className="min-h-screen bg-white">
        <div className="max-w-4xl mx-auto px-6 py-12">
          {/* 返回按钮 */}
          <button
            onClick={() => router.push('/study')}
            className="flex items-center gap-2 text-gray-600 hover:text-black mb-8 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            返回教材列表
          </button>

          {/* 文档标题 */}
          {selectedDoc && (
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-black mb-2">{selectedDoc.title}</h1>
              <p className="text-gray-600">共 {selectedDoc.total_chapters} 个章节</p>
            </div>
          )}

          {/* 章节列表 */}
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
            </div>
          ) : (
            <div className="space-y-4">
              {chapters.map((chapter, index) => (
                <motion.div
                  key={`chapter-${chapter.chapter_number}-${index}`}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className={`p-6 rounded-2xl border-2 ${
                    chapter.is_locked
                      ? 'bg-gray-50 border-gray-200 opacity-60'
                      : 'bg-white border-gray-200 hover:border-black hover:shadow-lg'
                  }`}
                >
                  <div className="flex items-center gap-4 mb-4">
                    {/* 章节图标 */}
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${
                      chapter.is_locked
                        ? 'bg-gray-200 text-gray-400'
                        : chapter.status === 'completed'
                        ? 'bg-green-100 text-green-600'
                        : 'bg-black text-white'
                    }`}>
                      {chapter.is_locked ? (
                        <Lock className="w-6 h-6" />
                      ) : chapter.status === 'completed' ? (
                        <CheckCircle2 className="w-6 h-6" />
                      ) : (
                        <span className="text-lg font-bold">{chapter.chapter_number}</span>
                      )}
                    </div>

                    {/* 章节信息 */}
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg text-black mb-1">
                        {chapter.chapter_title}
                      </h3>
                      <div className="flex items-center gap-4 text-sm">
                        <span className={`${
                          chapter.is_locked ? 'text-gray-400' : 'text-gray-600'
                        }`}>
                          {chapter.status_text}
                        </span>
                        {!chapter.is_locked && chapter.completion_percentage > 0 && (
                          <span className="text-gray-600">
                            完成度 {Math.round(chapter.completion_percentage)}%
                          </span>
                        )}
                      </div>
                      {chapter.is_locked && chapter.lock_reason && (
                        <p className="text-xs text-gray-500 mt-2">{chapter.lock_reason}</p>
                      )}
                    </div>
                  </div>

                  {/* 进度条 */}
                  {!chapter.is_locked && chapter.completion_percentage > 0 && (
                    <div className="mb-4 w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                      <motion.div
                        className="h-full bg-black rounded-full"
                        initial={{ width: 0 }}
                        animate={{ width: `${chapter.completion_percentage}%` }}
                        transition={{ duration: 0.8, ease: 'easeOut' }}
                      />
                    </div>
                  )}

                  {/* 小节列表 */}
                  {chapter.subsections && chapter.subsections.length > 0 && (
                    <div className="mb-4">
                      <button
                        onClick={() => setExpandedChapter(expandedChapter === chapter.chapter_number ? null : chapter.chapter_number)}
                        className="flex items-center gap-2 text-sm text-gray-600 hover:text-black mb-2 transition-colors"
                      >
                        <ChevronRight
                          className={`w-4 h-4 transition-transform ${
                            expandedChapter === chapter.chapter_number ? 'rotate-90' : ''
                          }`}
                        />
                        <span>{chapter.subsection_count}个小节</span>
                      </button>

                      <AnimatePresence>
                        {expandedChapter === chapter.chapter_number && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="overflow-hidden"
                          >
                            <div className="pl-6 pr-2 pb-2 space-y-1">
                              {chapter.subsections.map((subsection) => (
                                <button
                                  key={subsection.subsection_number}
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    router.push(`/study?doc=${docId}&chapter=${chapter.chapter_number}&subsection=${subsection.subsection_number}`)
                                  }}
                                  className="w-full text-left px-3 py-2 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors flex items-center gap-2 group"
                                >
                                  <span className="text-xs font-medium text-gray-500 group-hover:text-black">
                                    {subsection.subsection_number}
                                  </span>
                                  <span className="text-sm text-gray-700 group-hover:text-black flex-1">
                                    {subsection.subsection_title}
                                  </span>
                                  <MessageSquare className="w-3 h-3 text-gray-400 group-hover:text-black" />
                                </button>
                              ))}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  )}

                  {/* 操作按钮 */}
                  {!chapter.is_locked && (
                    <div className="flex gap-3">
                      <button
                        onClick={() => router.push(`/study?doc=${docId}&chapter=${chapter.chapter_number}`)}
                        className="flex-1 px-4 py-2 bg-black text-white rounded-xl hover:bg-gray-800 transition-colors flex items-center justify-center gap-2"
                      >
                        <MessageSquare className="w-4 h-4" />
                        <span>学习对话</span>
                      </button>
                      <button
                        onClick={() => router.push(`/quiz?doc=${docId}&chapter=${chapter.chapter_number}`)}
                        className="flex-1 px-4 py-2 border-2 border-black text-black rounded-xl hover:bg-black hover:text-white transition-colors flex items-center justify-center gap-2"
                      >
                        <BookOpen className="w-4 h-4" />
                        <span>章节测试</span>
                      </button>
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>
    )
  }

  // 3. 学习对话界面
  if (docId && chapterId && selectedChapter) {
    return (
      <div className="flex flex-col h-screen bg-white">
        {/* 顶部导航栏 */}
        <div className="border-b border-gray-200 bg-white">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              {/* 左侧：返回和标题 */}
              <div className="flex items-center gap-4">
                <button
                  onClick={() => router.push(`/study?doc=${docId}`)}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <ArrowLeft className="w-5 h-5 text-gray-600" />
                </button>
                <div>
                  <h1 className="font-semibold text-lg text-black">
                    {selectedChapter.chapter_title}
                  </h1>
                  <p className="text-sm text-gray-500">{selectedDoc?.title}</p>
                </div>
              </div>

              {/* 右侧：导师风格和进度 */}
              <div className="flex items-center gap-4">
                {/* 章节测试按钮 */}
                <button
                  onClick={() => router.push(`/quiz?doc=${docId}&chapter=${chapterId}`)}
                  className="px-4 py-2 border-2 border-black text-black rounded-xl hover:bg-black hover:text-white transition-colors flex items-center gap-2"
                >
                  <BookOpen className="w-4 h-4" />
                  <span className="text-sm font-medium">章节测试</span>
                </button>

                {/* 导师风格切换器 */}
                <div className="relative group">
                  <button className="flex items-center gap-3 px-4 py-2 bg-black text-white rounded-xl hover:bg-gray-800 transition-colors">
                    <Settings className="w-4 h-4" />
                    <span className="text-sm font-medium">
                      L{teachingStyle} {
                        teachingStyle === 1 ? '温柔' :
                        teachingStyle === 2 ? '耐心' :
                        teachingStyle === 3 ? '标准' :
                        teachingStyle === 4 ? '严格' : '严厉'
                      }
                    </span>
                  </button>

                  {/* 下拉菜单 */}
                  <div className="absolute right-0 top-full mt-2 w-56 bg-white rounded-xl shadow-lg border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
                    <div className="p-2">
                      <p className="text-xs text-gray-500 px-3 py-2">选择导师风格</p>
                      {[
                        { level: 1, label: 'L1 温柔', desc: '耐心细致，循序渐进' },
                        { level: 2, label: 'L2 耐心', desc: '详细讲解，注重基础' },
                        { level: 3, label: 'L3 标准', desc: '平衡严谨，注重应用' },
                        { level: 4, label: 'L4 严格', desc: '注重细节，深入理解' },
                        { level: 5, label: 'L5 严厉', desc: '挑战思维，独立解决' }
                      ].map((style) => (
                        <button
                          key={style.level}
                          onClick={() => handleStyleChange(style.level)}
                          className={`w-full text-left px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors ${
                            teachingStyle === style.level ? 'bg-gray-100' : ''
                          }`}
                        >
                          <div className="font-medium text-sm text-black">{style.label}</div>
                          <div className="text-xs text-gray-500">{style.desc}</div>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* 章节进度 */}
                {selectedChapter.completion_percentage > 0 && (
                  <div className="flex items-center gap-2">
                    <div className="w-32 h-2 bg-gray-100 rounded-full overflow-hidden">
                      <motion.div
                        className="h-full bg-black rounded-full"
                        initial={{ width: 0 }}
                        animate={{ width: `${selectedChapter.completion_percentage}%` }}
                        transition={{ duration: 0.8 }}
                      />
                    </div>
                    <span className="text-sm text-gray-600">
                      {Math.round(selectedChapter.completion_percentage)}%
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* 主学习区域 - 全屏对话 */}
        <div className="flex-1 overflow-hidden">
          <StudyChat
            chapterId={chapterId}
            chapterTitle={selectedChapter.chapter_title}
          />
        </div>
      </div>
    )
  }

  // 加载中
  return (
    <div className="flex items-center justify-center h-screen bg-white">
      <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
    </div>
  )
}

export default function StudyPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center h-screen bg-white">
        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    }>
      <StudyPageContent />
    </Suspense>
  )
}
