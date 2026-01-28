#!/usr/bin/env python3
"""初始化数据库脚本"""
import asyncio
import sys
import os

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(__file__))

from app.db.database import engine, init_db

async def main():
    """初始化数据库表"""
    try:
        await init_db()
        print('✅ 数据库已成功重建')
        print('📊 包含以下表：')
        print('   - users (用户表，包含 password 列)')
        print('   - documents (文档表)')
        print('   - progress (进度表)')
        print('   - conversations (对话历史表)')
        print('   - quiz_attempts (题目尝试表)')
    except Exception as e:
        print(f'❌ 初始化失败: {e}')
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
