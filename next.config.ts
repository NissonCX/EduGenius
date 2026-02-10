import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // 排除测试文件，避免在构建时被打包
  experimental: {
    serverComponentsExternalPackages: [],
  },
}

export default nextConfig
