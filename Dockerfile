# EduGenius 前端 Dockerfile
# 多阶段构建以优化镜像大小

# ==================== 阶段 1: 构建 ====================
FROM node:20-alpine AS builder

# 设置工作目录
WORKDIR /app

# 复制 package 文件
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production && \
    npm cache clean --force

# 复制源代码
COPY . .

# 设置构建时环境变量
ENV NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production

# 构建应用
RUN npm run build

# ==================== 阶段 2: 运行 ====================
FROM node:20-alpine AS runner

# 设置工作目录
WORKDIR /app

# 设置运行时环境变量
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000

# 创建非 root 用户
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# 复制必要的文件
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/next.config.ts ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# 切换到非 root 用户
USER nextjs

# 暴露端口
EXPOSE 3000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# 启动命令
CMD ["node", "server.js"]
