'use client'

/**
 * Documents Page - 文档管理主页
 * 显示所有已上传的文档
 */

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { FileText, Upload, Trash2, BookOpen, ArrowRight } from 'lucide-react'
import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'

export default function DocumentsPage() {
  const { user, isAuthenticated, getAuthHeaders } = useAuth()
  const [documents, setDocuments] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadDocuments = async () => {
      if (!isAuthenticated) return

      try {
        const response = await fetch('http://localhost:8000/api/documents/list', {
          headers: getAuthHeaders()
        })

        if (response.ok) {
          const data = await response.json()
          setDocuments(data.documents || [])
        }
      } catch (err) {
        console.error('Failed to load documents:', err)
      } finally {
        setLoading(false)
      }
    }

    loadDocuments()
  }, [isAuthenticated, getAuthHeaders])

  // 删除文档
  const handleDelete = async (documentId: number, title: string) => {
    if (!confirm(`确定要删除「${title}」吗？`)) return

    try {
      const response = await fetch(`http://localhost:8000/api/documents/${documentId}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      })

      if (response.ok) {
        setDocuments(prev => prev.filter(doc => doc.id !== documentId))
      } else {
        alert('删除失败')
      }
    } catch (err) {
      console.error('Delete error:', err)
      alert('删除失败')
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
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
                href="/documents/upload"
                className="px-4 py-2 bg-black text-white text-sm rounded-lg hover:bg-gray-800 transition-colors flex items-center gap-2"
              >
                <Upload className="w-4 h-4" />
                上传文档
              </Link>
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

      {/* 主内容 */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* 统计卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl">
            <p className="text-sm text-gray-600">文档总数</p>
            <p className="text-2xl font-semibold text-black mt-1">{documents.length}</p>
          </div>
          <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl">
            <p className="text-sm text-gray-600">已处理</p>
            <p className="text-2xl font-semibold text-black mt-1">
              {documents.filter(d => d.processing_status === 'completed').length}
            </p>
          </div>
          <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl">
            <p className="text-sm text-gray-600">总章节数</p>
            <p className="text-2xl font-semibold text-black mt-1">
              {documents.reduce((sum, doc) => sum + (doc.total_chapters || 0), 0)}
            </p>
          </div>
        </div>

        {/* 文档列表 */}
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-black"></div>
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-16 bg-gray-50 rounded-2xl border border-gray-200">
            <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-black mb-2">还没有文档</h2>
            <p className="text-gray-600 mb-6">上传你的第一份教材开始学习吧</p>
            <Link
              href="/documents/upload"
              className="px-6 py-3 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors inline-flex items-center gap-2"
            >
              <Upload className="w-5 h-5" />
              上传文档
            </Link>
          </div>
        ) : (
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase">文档名称</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase">类型</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase">章节</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 uppercase">状态</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-600 uppercase">操作</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {documents.map((doc, index) => (
                    <motion.tr
                      key={doc.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="hover:bg-gray-50 transition-colors"
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-gray-100 rounded-lg">
                            <FileText className="w-5 h-5 text-gray-600" />
                          </div>
                          <span className="font-medium text-black">{doc.title}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium uppercase rounded">
                          {doc.file_type}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-black">{doc.total_chapters} 章</td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          doc.processing_status === 'completed'
                            ? 'bg-gray-100 text-gray-700'
                            : 'bg-gray-50 text-gray-600'
                        }`}>
                          {doc.processing_status === 'completed' ? '✓ 已处理' : '处理中'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Link
                            href={`/study?doc=${doc.id}`}
                            className="px-3 py-1.5 bg-black text-white text-sm rounded-lg hover:bg-gray-800 transition-colors inline-flex items-center gap-1"
                          >
                            学习
                            <ArrowRight className="w-3.5 h-3.5" />
                          </Link>
                          <button
                            onClick={() => handleDelete(doc.id, doc.title)}
                            className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            title="删除"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
