import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // 启用 standalone 输出模式，用于 Docker 部署
  output: 'standalone',
}

export default nextConfig
