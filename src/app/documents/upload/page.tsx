'use client'

/**
 * Document Upload Page - 文档上传页面
 * 支持 PDF 和 TXT 文件上传
 * 极简黑白美学风格
 */

import { useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Upload, FileText, CheckCircle2, X, Loader2, BookOpen } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'

export default function DocumentUploadPage() {
  const router = useRouter()
  const { user, isAuthenticated, getAuthHeaders } = useAuth()
  const [files, setFiles] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadedDocs, setUploadedDocs] = useState<any[]>([])
  const [error, setError] = useState('')

  // 加载已上传的文档列表
  const loadDocuments = useCallback(async () => {
    if (!isAuthenticated) return

    try {
      const response = await fetch('http://localhost:8000/api/documents/list', {
        headers: getAuthHeaders()
      })

      if (response.ok) {
        const data = await response.json()
        setUploadedDocs(data.documents || [])
      }
    } catch (err) {
      console.error('Failed to load documents:', err)
    }
  }, [isAuthenticated, getAuthHeaders])

  // 页面加载时获取文档列表
  useState(() => {
    loadDocuments()
  })

  // 拖拽处理
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()

    const droppedFiles = Array.from(e.dataTransfer.files)
    validateAndAddFiles(droppedFiles)
  }

  // 文件选择
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files)
      validateAndAddFiles(selectedFiles)
    }
  }

  // 验证并添加文件
  const validateAndAddFiles = (newFiles: File[]) => {
    const validFiles: File[] = []
    const maxSize = 50 * 1024 * 1024 // 50MB

    for (const file of newFiles) {
      // 检查文件类型
      const ext = '.' + file.name.split('.').pop()?.toLowerCase()
      if (ext !== '.pdf' && ext !== '.txt') {
        setError(`不支持的文件类型: ${file.name}`)
        return
      }

      // 检查文件大小
      if (file.size > maxSize) {
        setError(`文件过大: ${file.name} (最大50MB)`)
        return
      }

      validFiles.push(file)
    }

    setFiles(prev => [...prev, ...validFiles])
    setError('')
  }

  // 移除文件
  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  // 上传文件
  const handleUpload = async () => {
    if (files.length === 0) {
      setError('请选择要上传的文件')
      return
    }

    setUploading(true)
    setUploadProgress(0)

    try {
      // 逐个上传文件
      for (let i = 0; i < files.length; i++) {
        const file = files[i]
        const formData = new FormData()
        formData.append('file', file)
        formData.append('title', file.name)

        const response = await fetch('http://localhost:8000/api/documents/upload', {
          method: 'POST',
          headers: getAuthHeaders(false), // false让浏览器自动设置Content-Type
          body: formData
        })

        setUploadProgress(((i + 1) / files.length) * 100)

        if (response.ok) {
          const result = await response.json()

          if (result.is_duplicate) {
            setError(`${file.name} 已存在`)
          }
        } else {
          const errorData = await response.json()
          setError(`上传失败: ${errorData.detail}`)
          setUploading(false)
          return
        }
      }

      // 上传完成，清空文件列表并刷新文档列表
      setFiles([])
      await loadDocuments()
      setUploading(false)
      setUploadProgress(0)

    } catch (err) {
      console.error('Upload error:', err)
      setError('网络错误，请稍后重试')
      setUploading(false)
    }
  }

  // 删除文档
  const handleDelete = async (documentId: number) => {
    if (!confirm('确定要删除这个文档吗？')) return

    try {
      const response = await fetch(`http://localhost:8000/api/documents/${documentId}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      })

      if (response.ok) {
        await loadDocuments()
      } else {
        alert('删除失败')
      }
    } catch (err) {
      console.error('Delete error:', err)
      alert('删除失败')
    }
  }

  // 未登录显示
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-semibold mb-4">文档上传</h1>
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
      <div className="border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between max-w-6xl mx-auto">
          <div className="flex items-center gap-3">
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

      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* 上传区域 */}
        <div className="mb-12">
          <h2 className="text-2xl font-semibold text-black mb-6">上传教材</h2>

          {/* 拖拽上传区域 */}
          <motion.div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
            className={`border-2 border-dashed rounded-2xl p-12 text-center transition-all ${
              files.length > 0
                ? 'border-black bg-gray-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-lg font-medium text-black mb-2">
              拖拽文件到此处，或点击选择文件
            </p>
            <p className="text-sm text-gray-500 mb-4">
              支持 PDF 和 TXT 文件，最大 50MB
            </p>
            <label className="inline-block">
              <input
                type="file"
                accept=".pdf,.txt"
                multiple
                onChange={handleFileSelect}
                className="hidden"
              />
              <span className="px-6 py-3 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors cursor-pointer inline-block">
                选择文件
              </span>
            </label>

            {/* 文件列表 */}
            {files.length > 0 && (
              <div className="mt-6 space-y-2">
                {files.map((file, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-black" />
                      <div>
                        <p className="text-sm font-medium text-black">{file.name}</p>
                        <p className="text-xs text-gray-500">
                          {(file.size / 1024).toFixed(1)} KB
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => removeFile(index)}
                      className="text-gray-400 hover:text-red-600 transition-colors"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </motion.div>
                ))}
              </div>
            )}

            {/* 上传按钮 */}
            {files.length > 0 && (
              <div className="mt-6">
                {error && (
                  <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                    {error}
                  </div>
                )}

                <motion.button
                  onClick={handleUpload}
                  disabled={uploading}
                  whileHover={{ scale: uploading ? 1 : 1.02 }}
                  whileTap={{ scale: uploading ? 1 : 0.98 }}
                  className="px-8 py-3 bg-black text-white rounded-lg hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors inline-flex items-center gap-2"
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
                </motion.button>
              </div>
            )}
          </motion.div>
        </div>

        {/* 已上传的文档列表 */}
        <div>
          <h2 className="text-2xl font-semibold text-black mb-6">我的文档</h2>

          {uploadedDocs.length === 0 ? (
            <div className="text-center py-16 bg-gray-50 rounded-2xl border border-gray-200">
              <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 mb-2">还没有上传任何文档</p>
              <p className="text-sm text-gray-500">上传 PDF 或 TXT 文件开始学习</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {uploadedDocs.map((doc) => (
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
                      onClick={() => handleDelete(doc.id)}
                      className="text-gray-400 hover:text-red-600 transition-colors"
                      title="删除文档"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>

                  <h3 className="font-semibold text-black mb-2 line-clamp-2">
                    {doc.title}
                  </h3>

                  <div className="space-y-2 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">类型</span>
                      <span className="font-medium text-black uppercase">
                        {doc.file_type}
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">状态</span>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        doc.processing_status === 'completed'
                          ? 'bg-gray-100 text-gray-700'
                          : 'bg-gray-50 text-gray-600'
                      }`}>
                        {doc.processing_status === 'completed' ? '✓ 已处理' : '处理中'}
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">章节数</span>
                      <span className="font-medium text-black">
                        {doc.total_chapters} 章
                      </span>
                    </div>
                  </div>

                  <Link
                    href={`/study?doc=${doc.id}`}
                    className="mt-4 block w-full px-4 py-2 bg-black text-white text-center text-sm rounded-lg hover:bg-gray-800 transition-colors"
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
