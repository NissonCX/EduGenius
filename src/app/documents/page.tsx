'use client'

/**
 * 文档管理页面 - 简化版
 * 集成上传和列表功能
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, FileText, Trash2, BookOpen, X, Loader2, CheckCircle2, AlertCircle } from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { getApiUrl, fetchWithTimeout, getAuthHeadersSimple } from '@/lib/config'
import { DocumentListSkeleton } from '@/components/ui/Skeleton'

interface Document {
  id: number
  filename: string
  title: string
  file_type: string
  file_size: number
  total_pages: number
  total_chapters: number
  processing_status: string
  uploaded_at: string
  md5_hash: string
}

export default function DocumentsPage() {
  const router = useRouter()

  // 文档列表
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)

  // 上传状态
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error' | 'partial'>('idle')
  const [uploadMessage, setUploadMessage] = useState('')

  // 用户信息（避免 hydration 问题）
  const [username, setUsername] = useState<string>('用户')
  const [mounted, setMounted] = useState(false)

  // 跟踪组件是否已挂载，用于 setTimeout 清理
  const isMountedRef = useRef(true)

  // 错误提示状态
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // 客户端挂载后读取用户信息
  useEffect(() => {
    setMounted(true)
    isMountedRef.current = true
    const userStr = localStorage.getItem('user')
    if (userStr) {
      try {
        const user = JSON.parse(userStr)
        setUsername(user.username || '用户')
      } catch {
        setUsername('用户')
      }
    }
    return () => {
      isMountedRef.current = false
    }
  }, [])

  // 加载文档列表
  const loadDocuments = useCallback(async () => {
    console.log('🔄 开始加载文档列表...')
    try {
      // 🔧 使用带超时的fetch（10秒超时）和简化的认证头
      const apiUrl = getApiUrl('/api/documents/list')
      console.log('📡 API URL:', apiUrl)
      console.log('🔑 Token 存在?', !!localStorage.getItem('token'))

      const response = await fetchWithTimeout(
        apiUrl,
        {
          method: 'GET',
          headers: getAuthHeadersSimple()
        },
        30000  // 30秒超时（后端可能处理慢）
      )

      console.log('📥 响应状态:', response.status, response.statusText)

      if (response.ok) {
        const data = await response.json()
        const docs = data.documents || []
        setDocuments(docs)

        // 检查是否有正在处理的文档
        const hasProcessing = docs.some((doc: Document) =>
          doc.processing_status === 'processing' ||
          doc.processing_status === 'ocr_processing' ||
          doc.processing_status === 'pending'
        )
        return hasProcessing  // 返回是否还有正在处理的文档
      }
      return false
    } catch (err) {
      console.error('加载文档失败:', err)
      return false
    } finally {
      setLoading(false)
    }
  }, [])

  // 轮询设置
  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null
    let isMounted = true

    const startPolling = async () => {
      try {
        // 页面可见时立即加载一次
        const hasProcessing = await loadDocuments()

        // 检查组件是否仍然挂载
        if (!isMounted) return

        // 如果有正在处理的文档，启动轮询
        if (hasProcessing) {
          intervalId = setInterval(async () => {
            const stillProcessing = await loadDocuments()
            // 如果没有正在处理的文档了，停止轮询
            if (!stillProcessing && intervalId) {
              clearInterval(intervalId)
              intervalId = null
            }
          }, 3000)  // 每3秒轮询一次
        }
      } catch (err) {
        console.error('轮询失败:', err)
      }
    }

    startPolling()

    // 清理函数
    return () => {
      isMounted = false
      if (intervalId) {
        clearInterval(intervalId)
      }
    }
  }, [loadDocuments])

  // 文件选择
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files)
      const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50MB
      const SUPPORTED_FORMATS = ['pdf', 'txt', 'docx', 'pptx', 'docm']

      const validFiles = files.filter(file => {
        const ext = file.name.split('.').pop()?.toLowerCase()
        const isValidType = ext && SUPPORTED_FORMATS.includes(ext)
        const isValidSize = file.size <= MAX_FILE_SIZE

        if (!isValidType) {
          setUploadMessage(`文件 ${file.name} 格式不支持，支持格式：${SUPPORTED_FORMATS.join(', ').toUpperCase()}`)
          setUploadStatus('error')
          return false
        }

        if (!isValidSize) {
          setUploadMessage(`文件 ${file.name} 超过 50MB 限制（当前 ${(file.size / 1024 / 1024).toFixed(1)}MB）`)
          setUploadStatus('error')
          return false
        }

        return true
      })

      if (validFiles.length > 0) {
        setSelectedFiles(validFiles)
        setUploadStatus('idle')
        setUploadMessage('')
      }
    }
  }

  // 上传文件（增强版 - 支持并行上传）
  const handleUpload = async () => {
    if (selectedFiles.length === 0) return

    setUploading(true)
    setUploadStatus('uploading')
    setUploadProgress(0)
    setUploadMessage('')

    // 并发上传队列（最多同时 3 个文件）
    const CONCURRENT_UPLOADS = 3
    const uploadQueue = [...selectedFiles]
    const results: { file: string; success: boolean; error?: string }[] = []
    let completed = 0

    try {
      // 并发上传函数
      const uploadFile = async (file: File): Promise<{ file: string; success: boolean; error?: string }> => {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('title', file.name)

        try {
          const response = await fetch(getApiUrl('/api/documents/upload'), {
            method: 'POST',
            headers: getAuthHeadersSimple(false),
            body: formData
          })

          if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: '上传失败' }))
            return { file: file.name, success: false, error: error.detail || '上传失败' }
          }

          return { file: file.name, success: true }
        } catch (error: any) {
          return { file: file.name, success: false, error: error.message }
        }
      }

      // 分批处理
      while (uploadQueue.length > 0) {
        const batch = uploadQueue.splice(0, CONCURRENT_UPLOADS)
        const batchResults = await Promise.all(batch.map(file => uploadFile(file)))

        results.push(...batchResults)
        completed += batchResults.length

        // 更新进度
        setUploadProgress((completed / selectedFiles.length) * 100)

        // 更新状态消息
        const successCount = results.filter(r => r.success).length
        setUploadMessage(`正在上传: ${successCount}/${selectedFiles.length} 完成`)
      }

      // 检查结果
      const successCount = results.filter(r => r.success).length
      const failedResults = results.filter(r => !r.success)

      if (failedResults.length === 0) {
        setUploadStatus('success')
        setUploadMessage(`✅ 成功上传 ${successCount} 个文件`)
        setSelectedFiles([])

        // 刷新列表
        await loadDocuments()

        // 3秒后重置状态
        setTimeout(() => {
          if (isMountedRef.current) {
            setUploadStatus('idle')
            setUploadMessage('')
          }
        }, 3000)
      } else {
        setUploadStatus('partial')
        const failedNames = failedResults.map(r => r.file).join(', ')
        setUploadMessage(`⚠️ ${successCount}/${selectedFiles.length} 成功\n失败: ${failedNames}`)

        // 5秒后重置状态
        setTimeout(() => {
          if (isMountedRef.current) {
            setUploadStatus('idle')
            setUploadMessage('')
          }
        }, 5000)
      }

    } catch (error: any) {
      setUploadStatus('error')
      setUploadMessage(error.message || '上传失败')
    } finally {
      setUploading(false)
    }
  }

  // 删除文档
  const handleDelete = async (documentId: number, title: string) => {
    if (!confirm(`确定要删除「${title}」吗？`)) return

    try {
      const response = await fetch(getApiUrl(`/api/documents/${documentId}`), {
        method: 'DELETE',
        headers: getAuthHeadersSimple()
      })

      if (response.ok) {
        setDocuments(prev => prev.filter(doc => doc.id !== documentId))
      } else {
        setErrorMessage('删除失败，请稍后重试')
        setTimeout(() => {
          if (isMountedRef.current) {
            setErrorMessage(null)
          }
        }, 3000)
      }
    } catch (err) {
      console.error('删除失败:', err)
      setErrorMessage('删除失败，请稍后重试')
      setTimeout(() => {
        if (isMountedRef.current) {
          setErrorMessage(null)
        }
      }, 3000)
    }
  }

  return (
    <div className="min-h-screen bg-white">
      {/* 错误提示 */}
      <AnimatePresence>
        {errorMessage && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="fixed top-4 left-1/2 -translate-x-1/2 z-50"
          >
            <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg shadow-lg flex items-center gap-2">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span className="text-sm font-medium">{errorMessage}</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 顶部导航 */}
      <div className="border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <BookOpen className="w-6 h-6 text-black" />
              <h1 className="text-xl font-semibold text-black">文档管理</h1>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">{mounted ? username : '用户'}</span>
              <Link
                href="/study"
                className="text-sm text-gray-600 hover:text-black transition-colors"
              >
                返回学习
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* 上传区域 */}
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-4">上传教材</h2>
          
          <div className="border-2 border-dashed border-gray-300 rounded-xl p-8">
            <div className="text-center">
              <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-sm text-gray-600 mb-4">
                支持 PDF、TXT、Word (DOCX)、PowerPoint (PPTX) 文件，最大 50MB
              </p>

              <label className="inline-block">
                <input
                  type="file"
                  accept=".pdf,.txt,.docx,.pptx,.docm"
                  multiple
                  onChange={handleFileSelect}
                  className="hidden"
                  disabled={uploading}
                />
                <span className="px-6 py-2 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors cursor-pointer inline-block text-sm">
                  选择文件
                </span>
              </label>
            </div>

            {/* 已选文件 */}
            {selectedFiles.length > 0 && (
              <div className="mt-6 space-y-2">
                {selectedFiles.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-gray-600" />
                      <div>
                        <p className="text-sm font-medium">{file.name}</p>
                        <p className="text-xs text-gray-500">
                          {(file.size / 1024).toFixed(1)} KB
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => setSelectedFiles(prev => prev.filter((_, i) => i !== index))}
                      className="text-gray-400 hover:text-red-600"
                      disabled={uploading}
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>
                ))}

                <button
                  onClick={handleUpload}
                  disabled={uploading}
                  className="w-full mt-4 px-6 py-3 bg-black text-white rounded-lg hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      上传中... {Math.round(uploadProgress)}%
                    </>
                  ) : (
                    <>
                      <Upload className="w-5 h-5" />
                      开始上传
                    </>
                  )}
                </button>
              </div>
            )}

            {/* 上传状态 */}
            <AnimatePresence>
              {uploadMessage && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className={`mt-4 p-3 rounded-lg flex items-center gap-2 ${
                    uploadStatus === 'success' ? 'bg-green-50 text-green-700' :
                    uploadStatus === 'error' ? 'bg-red-50 text-red-700' :
                    'bg-blue-50 text-blue-700'
                  }`}
                >
                  {uploadStatus === 'success' && <CheckCircle2 className="w-5 h-5" />}
                  {uploadStatus === 'error' && <AlertCircle className="w-5 h-5" />}
                  <span className="text-sm">{uploadMessage}</span>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* 文档列表 */}
        <div>
          <h2 className="text-lg font-semibold mb-4">我的文档</h2>

          {/* 加载中 - 显示骨架屏 */}
          {loading ? (
            <DocumentListSkeleton count={6} />
          ) : documents.length === 0 ? (
            <div className="text-center py-16 bg-gray-50 rounded-xl">
              <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">还没有上传任何文档</p>
            </div>
          ) : (
            <>
              {/* 处理中的文档提示 */}
              {documents.some(doc =>
                doc.processing_status === 'processing' ||
                doc.processing_status === 'ocr_processing' ||
                doc.processing_status === 'pending'
              ) && (
                <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-xl flex items-center gap-3">
                  <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-blue-900">
                      有文档正在处理中
                    </p>
                    <p className="text-xs text-blue-700">
                      您可以继续浏览其他内容，处理完成后会自动更新
                    </p>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {documents.map((doc) => {
                  const isProcessing =
                    doc.processing_status === 'processing' ||
                    doc.processing_status === 'ocr_processing' ||
                    doc.processing_status === 'pending'

                  return (
                    <motion.div
                      key={doc.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`p-6 border rounded-xl transition-all ${
                        isProcessing
                          ? 'bg-blue-50 border-blue-200'
                          : 'bg-white border-gray-200 hover:shadow-md'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-4">
                        <div className={`p-3 rounded-lg ${
                          isProcessing
                            ? 'bg-blue-100 text-blue-600'
                            : 'bg-black text-white'
                        }`}>
                          {isProcessing ? (
                            <Loader2 className="w-6 h-6 animate-spin" />
                          ) : (
                            <FileText className="w-6 h-6" />
                          )}
                        </div>
                        <button
                          onClick={() => handleDelete(doc.id, doc.title)}
                          className="text-gray-400 hover:text-red-600 transition-colors"
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </div>

                      <h3 className="font-semibold text-black mb-2 line-clamp-2">
                        {doc.title}
                      </h3>

                      <div className="space-y-2 text-sm mb-4">
                        <div className="flex justify-between">
                          <span className="text-gray-600">类型</span>
                          <span className="font-medium uppercase">{doc.file_type}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">章节</span>
                          <span className="font-medium">{doc.total_chapters} 章</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">状态</span>
                          <span className={`px-2 py-0.5 rounded text-xs flex items-center gap-1 ${
                            doc.processing_status === 'completed'
                              ? 'bg-green-100 text-green-700'
                              : 'bg-blue-100 text-blue-700'
                          }`}>
                            {doc.processing_status === 'completed' ? (
                              <>✓ 已处理</>
                            ) : (
                              <>
                                <Loader2 className="w-3 h-3 animate-spin" />
                                处理中
                              </>
                            )}
                          </span>
                        </div>
                      </div>

                      <Link
                        href={`/study?doc=${doc.id}`}
                        className={`block w-full px-4 py-2 text-center text-sm rounded-lg transition-colors ${
                          isProcessing
                            ? 'bg-blue-100 text-blue-600 cursor-not-allowed'
                            : 'bg-black text-white hover:bg-gray-800'
                        }`}
                        onClick={(e) => {
                          if (isProcessing) {
                            e.preventDefault()
                          }
                        }}
                      >
                        {isProcessing ? '处理中...' : '开始学习'}
                      </Link>
                    </motion.div>
                  )
                })}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
