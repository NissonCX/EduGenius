'use client'

import { motion } from 'framer-motion'
import { BookOpen, Sparkles, Target, Zap } from 'lucide-react'
import Link from 'next/link'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="container-x py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="max-w-3xl"
        >
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full border border-gray-200 bg-gray-50/50 mb-6">
            <Sparkles className="w-4 h-4 text-black" />
            <span className="text-sm">AI 驱动的个性化学习体验</span>
          </div>

          <h1 className="text-5xl font-semibold tracking-tight text-balance mb-6">
            让学习<span className="text-gray-500">适应你的节奏</span>
          </h1>

          <p className="text-xl text-gray-500 leading-relaxed mb-8">
            EduGenius 采用先进的 LangGraph 多智能体架构，根据你的认知深度（L1-L5）
            动态调整教学策略，提供真正的个性化学习体验。
          </p>

          <div className="flex items-center space-x-4">
            <Link href="/documents">
              <motion.button
                className="px-6 py-3 bg-black text-white rounded-xl font-medium shadow-sm hover:shadow-md transition-all duration-200"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                上传文档
              </motion.button>
            </Link>
            <Link href="/study">
              <motion.button
                className="px-6 py-3 border border-gray-200 rounded-xl font-medium hover:bg-gray-50/50 transition-all duration-200"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                开始学习
              </motion.button>
            </Link>
          </div>
        </motion.div>
      </section>

      {/* Features Grid */}
      <section className="container-x py-20 border-t border-gray-200">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="text-2xl font-semibold mb-12">核心特性</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                icon: BookOpen,
                title: '智能教材解析',
                description: '上传 PDF/TXT 文件，系统自动进行 MD5 校验并智能解析内容结构'
              },
              {
                icon: Target,
                title: '认知深度评估',
                description: 'L1-L5 五级认知体系，精准定位你的学习阶段与理解深度'
              },
              {
                icon: Zap,
                title: '多智能体协作',
                description: '架构师、考官、导师三大 AI 智能体协同工作，提供全方位学习支持'
              }
            ].map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
                className="card-base p-6 interactive"
              >
                <feature.icon className="w-8 h-8 mb-4 text-black" />
                <h3 className="text-lg font-medium mb-2">{feature.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* AI Agents Section */}
      <section className="container-x py-20 border-t border-gray-200">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="text-2xl font-semibold mb-4">AI 智能体架构</h2>
          <p className="text-gray-500 mb-12 max-w-2xl">
            基于 LangGraph 构建的多智能体系统，每个智能体专注于特定任务，协同提供最佳学习体验
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                role: '架构师',
                color: 'bg-blue-500',
                description: '分析教材结构，设计学习路径，规划知识图谱'
              },
              {
                role: '考官',
                color: 'bg-emerald-500',
                description: '生成评估题目，分析答题情况，定位知识薄弱点'
              },
              {
                role: '导师',
                color: 'bg-purple-500',
                description: '提供个性化讲解，调整教学策略，解答学习疑问'
              }
            ].map((agent, index) => (
              <motion.div
                key={agent.role}
                initial={{ opacity: 0, scale: 0.95 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
                className="card-base p-6 text-center interactive"
              >
                <div className={`w-16 h-16 ${agent.color} rounded-2xl mx-auto mb-4 flex items-center justify-center`}>
                  <span className="text-white text-2xl font-semibold">
                    {agent.role[0]}
                  </span>
                </div>
                <h3 className="text-lg font-medium mb-2">{agent.role}</h3>
                <p className="text-sm text-gray-500">
                  {agent.description}
                </p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </section>
    </div>
  )
}
