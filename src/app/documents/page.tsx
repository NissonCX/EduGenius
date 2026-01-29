'use client'

/**
 * 文档管理页面 - 简化版
 * 集成上传和列表功能
 */

import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, FileText, Trash2, BookOpen, X, Loader2, CheckCircle2, AlertCircle } from 'lucide-react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { getApiUrl } from '@/lib/config'

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
  const { user, isAuthenticated, getAuthHeaders } = useAuth()
  
  // 文档列表
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  
  // 上传状态
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle')
  const [uploadMessage, setUploadMessage] = useState('')

  // 加载文档列表
  const loadDocuments = useCallback(async () => {
    if (!isAuthenticated) {
      setLoading(false)
      return
    }

    try {
      const response = await fetch(getApiUrl('/api/documents/list'), {
        headers: getAuthHeaders()  // 直接调用，不作为依赖
      })

      if (response.ok) {
        const data = await response.json()
        const docs = data.documents || []
        setDocuments(docs)

        // 检查是否有正在处理的文档
        const hasProcessing = docs.some((doc: Document) => doc.processing_status === 'processing')
        return hasProcessing  // 返回是否还有正在处理的文档
      }
      return false
    } catch (err) {
      console.error('加载文档失败:', err)
      return false
    } finally {
      setLoading(false)
    }
  }, [isAuthenticated])

  // 轮询设置
  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null

    const startPolling = async () => {
      const hasProcessing = await loadDocuments()

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
    }

    startPolling()

    // 清理函数
    return () => {
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
      
      const validFiles = files.filter(file => {
        const ext = file.name.split('.').pop()?.toLowerCase()
        const isValidType = ext === 'pdf' || ext === 'txt'
        const isValidSize = file.size <= MAX_FILE_SIZE
        
        if (!isValidType) {
          setUploadMessage(`文件 ${file.name} 格式不支持，只支持 PDF 和 TXT`)
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

  // 上传文件
  const handleUpload = async () => {
    if (selectedFiles.length === 0) return

    setUploading(true)
    setUploadStatus('uploading')
    setUploadProgress(0)
    setUploadMessage('')

    try {
      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i]
        const formData = new FormData()
        formData.append('file', file)
        formData.append('title', file.name)

        const response = await fetch(getApiUrl('/api/documents/upload'), {
          method: 'POST',
          headers: getAuthHeaders(false),
          body: formData
        })

        setUploadProgress(((i + 1) / selectedFiles.length) * 100)

        if (!response.ok) {
          const error = await response.json().catch(() => ({ detail: '上传失败' }))
          throw new Error(error.detail || '上传失败')
        }
      }

      setUploadStatus('success')
      setUploadMessage(`成功上传 ${selectedFiles.length} 个文件`)
      setSelectedFiles([])
      
      // 刷新列表
      await loadDocuments()
      
      // 3秒后重置状态
      setTimeout(() => {
        setUploadStatus('idle')
        setUploadMessage('')
      }, 3000)
      
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
        headers: getAuthHeaders()
      })

      if (response.ok) {
        setDocuments(prev => prev.filter(doc => doc.id !== documentId))
      } else {
        alert('删除失败')
      }
    } catch (err) {
      console.error('删除失败:', err)
      alert('删除失败')
    }
  }

  // 未登录
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <BookOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h1 className="text-2xl font-semibold mb-4">文档管理</h1>
          <p className="text-gray-500 mb-6">请先登录以使用文档管理功能</p>
          <Link
            href="/login"
            className="px-6 py-3 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors inline-block"
          >
            前往登录
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white">
      {/* 顶部导航 */}
      <div className="border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <BookOpen className="w-6 h-6 text-black" />
              <h1 className="text-xl font-semibold text-black">文档管理</h1>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">{user.username}</span>
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
                支持 PDF 和 TXT 文件，最大 50MB
              </p>
              
              <label className="inline-block">
                <input
                  type="file"
                  accept=".pdf,.txt"
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

          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
            </div>
          ) : documents.length === 0 ? (
            <div className="text-center py-16 bg-gray-50 rounded-xl">
              <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">还没有上传任何文档</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {documents.map((doc) => (
                <motion.div
                  key={doc.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-6 bg-white border border-gray-200 rounded-xl hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="p-3 bg-black text-white rounded-lg">
                      <FileText className="w-6 h-6" />
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
                    <div className="flex justify-between">
                      <span className="text-gray-600">状态</span>
                      <span className={`px-2 py-0.5 rounded text-xs ${
                        doc.processing_status === 'completed'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-yellow-100 text-yellow-700'
                      }`}>
                        {doc.processing_status === 'completed' ? '✓ 已处理' : '处理中'}
                      </span>
                    </div>
                  </div>

                  <Link
                    href={`/study?doc=${doc.id}`}
                    className="block w-full px-4 py-2 bg-black text-white text-center text-sm rounded-lg hover:bg-gray-800 transition-colors"
                  >
                    开始学习
                  </Link>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
