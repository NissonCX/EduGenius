'use client'

/**
 * 智能文档上传组件
 *
 * 支持混合处理架构：
 * 1. 预检测 PDF 文本层
 * 2. 快速路径（有文本层）或 OCR 路径（扫描件）
 * 3. 实时进度展示
 * 4. OCR 完成后显示特殊标签
 */

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, FileText, CheckCircle2, Loader2, AlertCircle, Eye, Sparkles } from 'lucide-react'
import { getApiUrl } from '@/lib/config'

// 处理阶段
type ProcessingStage =
  | 'idle'           // 未开始
  | 'uploading'      // 上传中
  | 'detecting'      // 检测PDF类型
  | 'processing'     // 快速路径处理中
  | 'ocr_processing' // OCR识别中
  | 'vectorizing'    // 向量化存储
  | 'completed'      // 完成
  | 'failed'         // 失败

interface ProcessingStatus {
  document_id: number
  status: string
  stage: string
  stage_message: string
  progress_percentage: number
  has_text_layer: boolean
  ocr_confidence: number
  current_page: number
  total_pages: number
  is_scan: boolean
  warning?: string
  ocr_notice?: string
}

interface SmartUploadProps {
  onUploadComplete?: (documentId: number) => void
  onError?: (error: string) => void
}

export function SmartUpload({ onUploadComplete, onError }: SmartUploadProps) {
  const [file, setFile] = useState<File | null>(null)
  const [stage, setStage] = useState<ProcessingStage>('idle')
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState<ProcessingStatus | null>(null)
  const [error, setError] = useState<string>('')

  const fileInputRef = useRef<HTMLInputElement>(null)
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const documentIdRef = useRef<number | null>(null)

  // 清理轮询
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
      }
    }
  }, [])

  // 处理文件选择
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (!selectedFile) return

    // 验证文件类型
    if (!selectedFile.name.toLowerCase().endsWith('.pdf')) {
      setError('请上传 PDF 文件')
      return
    }

    // 验证文件大小（50MB）
    if (selectedFile.size > 50 * 1024 * 1024) {
      setError('文件大小不能超过 50MB')
      return
    }

    setFile(selectedFile)
    setError('')
    setStage('uploading')
    setProgress(0)

    // 开始上传
    uploadFile(selectedFile)
  }

  // 上传文件
  const uploadFile = async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('title', file.name.replace('.pdf', ''))

    try {
      // 模拟上传进度
      let uploadProgress = 0
      const uploadInterval = setInterval(() => {
        uploadProgress += 10
        setProgress(uploadProgress)
        if (uploadProgress >= 90) {
          clearInterval(uploadInterval)
        }
      }, 200)

      const response = await fetch(getApiUrl('/api/documents/upload'), {
        method: 'POST',
        body: formData,
      })

      clearInterval(uploadInterval)

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || '上传失败')
      }

      const result = await response.json()

      // 保存文档ID
      documentIdRef.current = result.document_id

      // 开始轮询进度
      setStage('detecting')
      pollProgress(result.document_id)

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '上传失败'
      setError(errorMessage)
      setStage('failed')
      onError?.(errorMessage)
    }
  }

  // 轮询处理进度
  const pollProgress = async (documentId: number) => {
    try {
      const response = await fetch(getApiUrl(`/api/documents/${documentId}/status`))

      if (!response.ok) {
        throw new Error('获取进度失败')
      }

      const data: ProcessingStatus = await response.json()
      setStatus(data)

      // 更新进度和阶段
      setProgress(data.progress_percentage)

      // 根据状态映射到UI阶段
      if (data.status === 'completed') {
        setStage('completed')
        setProgress(100)
        onUploadComplete?.(documentId)
        return
      } else if (data.status === 'failed') {
        setStage('failed')
        setError(data.stage_message || '处理失败，请重新上传')
        return
      } else if (data.status === 'ocr_processing') {
        setStage('ocr_processing')
      } else if (data.status === 'processing') {
        setStage('processing')
      } else if (data.status === 'pending') {
        setStage('detecting')
      }

      // 继续轮询（每2秒）
      pollIntervalRef.current = setTimeout(() => {
        pollProgress(documentId)
      }, 2000)

    } catch (err) {
      console.error('轮询进度失败:', err)
      // 继续轮询
      pollIntervalRef.current = setTimeout(() => {
        pollProgress(documentId)
      }, 2000)
    }
  }

  // 重新上传
  const handleReset = () => {
    setFile(null)
    setStage('idle')
    setProgress(0)
    setStatus(null)
    setError('')
    if (pollIntervalRef.current) {
      clearTimeout(pollIntervalRef.current)
    }
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* 上传区域 */}
      <AnimatePresence mode="wait">
        {stage === 'idle' && (
          <motion.div
            key="upload"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            <div
              onClick={() => fileInputRef.current?.click()}
              className="group relative cursor-pointer"
            >
              {/* 玻璃态卡片 */}
              <div className="glass-card bg-white/80 backdrop-blur-xl border-2 border-dashed border-gray-300 hover:border-black rounded-3xl p-12 transition-all duration-300 group-hover:shadow-xl">
                {/* 上传图标 */}
                <div className="flex flex-col items-center">
                  <motion.div
                    className="w-20 h-20 bg-gradient-to-br from-black to-gray-800 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300"
                    whileHover={{ rotate: 5 }}
                  >
                    <Upload className="w-10 h-10 text-white" />
                  </motion.div>

                  {/* 标题 */}
                  <h3 className="text-xl font-semibold text-black mb-2">
                    上传教材 PDF
                  </h3>

                  {/* 描述 */}
                  <p className="text-gray-600 mb-4 text-center">
                    拖拽文件到此处，或点击选择文件
                  </p>

                  {/* 提示 */}
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <FileText className="w-4 h-4" />
                    <span>支持 PDF 格式，最大 50MB</span>
                  </div>

                  {/* 智能处理提示 */}
                  <div className="mt-6 flex items-center gap-2 px-4 py-2 bg-blue-50 rounded-xl">
                    <Sparkles className="w-4 h-4 text-blue-600" />
                    <span className="text-sm text-blue-900">
                      智能识别：自动检测PDF类型并选择最佳处理方式
                    </span>
                  </div>
                </div>

                {/* 隐藏的文件输入 */}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,application/pdf"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </div>
            </div>
          </motion.div>
        )}

        {/* 处理进度界面 */}
        {(stage !== 'idle' && stage !== 'failed') && (
          <motion.div
            key="processing"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.3 }}
            className="glass-card bg-white/90 backdrop-blur-xl border border-gray-200 rounded-3xl p-8 shadow-xl"
          >
            {/* 文件信息 */}
            <div className="flex items-center gap-4 mb-6">
              <div className="w-16 h-16 bg-gradient-to-br from-black to-gray-800 rounded-2xl flex items-center justify-center flex-shrink-0">
                <FileText className="w-8 h-8 text-white" />
              </div>

              <div className="flex-1 min-w-0">
                <h3 className="text-lg font-semibold text-black truncate">
                  {file?.name || '文档'}
                </h3>
                <p className="text-sm text-gray-600">
                  {status?.stage_message || '正在处理...'}
                </p>
              </div>

              {/* OCR 标签 */}
              {status?.is_scan && stage === 'completed' && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="flex-shrink-0 px-3 py-1.5 bg-orange-100 text-orange-700 rounded-lg text-sm font-medium flex items-center gap-1.5"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>OCR识别</span>
                </motion.div>
              )}
            </div>

            {/* 进度条 */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">处理进度</span>
                <span className="text-sm font-semibold text-black">{progress}%</span>
              </div>

              {/* 进度条背景 */}
              <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                {/* 渐变进度条 */}
                <motion.div
                  className="h-full bg-gradient-to-r from-blue-500 to-green-500 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.5, ease: 'easeOut' }}
                />
              </div>
            </div>

            {/* 阶段指示器 */}
            <div className="space-y-3">
              {/* 检测阶段 */}
              <ProcessingStep
                icon={<Sparkles className="w-5 h-5" />}
                label="检测PDF类型"
                active={stage === 'detecting'}
                completed={stage !== 'detecting' && stage !== 'uploading'}
              />

              {/* 处理阶段（根据路径显示） */}
              {status?.has_text_layer ? (
                <>
                  {/* 快速路径 */}
                  <ProcessingStep
                    icon={<Loader2 className="w-5 h-5" />}
                    label="提取文本内容"
                    active={stage === 'processing'}
                    completed={stage !== 'processing' && stage !== 'detecting' && stage !== 'uploading'}
                  />
                </>
              ) : (
                <>
                  {/* OCR 路径 */}
                  <ProcessingStep
                    icon={<Eye className="w-5 h-5" />}
                    label="OCR识别"
                    subtext={status?.current_page > 0 ? `${status.current_page}/${status.total_pages}页` : ''}
                    active={stage === 'ocr_processing'}
                    completed={stage === 'completed' && status?.is_scan}
                  />
                </>
              )}

              {/* 向量化阶段 */}
              <ProcessingStep
                icon={<CheckCircle2 className="w-5 h-5" />}
                label="向量化存储"
                active={stage === 'vectorizing'}
                completed={stage === 'completed'}
              />

              {/* 完成状态 */}
              {stage === 'completed' && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center gap-3 p-4 bg-green-50 rounded-xl border border-green-200"
                >
                  <CheckCircle2 className="w-6 h-6 text-green-600" />
                  <div className="flex-1">
                    <p className="font-semibold text-green-900">处理完成！</p>
                    {status?.warning && (
                      <p className="text-sm text-green-700 mt-1">{status.warning}</p>
                    )}
                  </div>
                </motion.div>
              )}
            </div>

            {/* OCR 警告提示 */}
            {status?.ocr_notice && stage === 'completed' && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-6 p-4 bg-amber-50 rounded-xl border border-amber-200"
              >
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-amber-900">{status.ocr_notice}</p>
                  </div>
                </div>
              </motion.div>
            )}
          </motion.div>
        )}

        {/* 错误状态 */}
        {stage === 'failed' && (
          <motion.div
            key="error"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="glass-card bg-white/90 backdrop-blur-xl border border-red-200 rounded-3xl p-8 shadow-xl"
          >
            <div className="text-center">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <AlertCircle className="w-8 h-8 text-red-600" />
              </div>

              <h3 className="text-xl font-semibold text-red-900 mb-2">
                处理失败
              </h3>

              <p className="text-gray-600 mb-6">
                {error}
              </p>

              <button
                onClick={handleReset}
                className="px-6 py-3 bg-black text-white rounded-xl hover:bg-gray-800 transition-colors font-medium"
              >
                重新上传
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// 处理步骤组件
interface ProcessingStepProps {
  icon: React.ReactNode
  label: string
  subtext?: string
  active?: boolean
  completed?: boolean
}

function ProcessingStep({ icon, label, subtext, active, completed }: ProcessingStepProps) {
  return (
    <div className="flex items-center gap-3">
      {/* 图标 */}
      <div className={`
        w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 transition-all duration-300
        ${completed ? 'bg-green-100 text-green-600' : ''}
        ${active ? 'bg-blue-100 text-blue-600' : ''}
        ${!completed && !active ? 'bg-gray-100 text-gray-400' : ''}
      `}>
        {active ? (
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          >
            {icon}
          </motion.div>
        ) : (
          icon
        )}
      </div>

      {/* 标签和副文本 */}
      <div className="flex-1">
        <p className={`
          font-medium transition-colors duration-300
          ${completed ? 'text-green-700' : ''}
          ${active ? 'text-blue-700' : ''}
          ${!completed && !active ? 'text-gray-600' : ''}
        `}>
          {label}
        </p>
        {subtext && (
          <p className="text-sm text-gray-500 mt-0.5">{subtext}</p>
        )}
      </div>

      {/* 状态指示器 */}
      {completed && (
        <CheckCircle2 className="w-5 h-5 text-green-600" />
      )}
    </div>
  )
}
