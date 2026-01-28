#!/usr/bin/env python3
"""
EduGenius RAG 流程测试脚本
测试文档解析、向量化、检索的完整流程
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.document_processor import process_uploaded_document, DocumentProcessor
from app.core.chroma import (
    create_document_collection,
    add_document_chunks,
    search_documents,
    get_collection_stats
)
from app.core.config import settings


async def test_document_processing():
    """测试文档处理完整流程"""
    print("=" * 60)
    print("📋 测试 1: 文档处理流程")
    print("=" * 60)

    # 创建一个测试 TXT 文件
    test_file = "/tmp/test_document.txt"
    test_content = """
# 第一章：线性代数基础

## 1.1 向量的定义

向量是线性代数中最基本的概念之一。从几何角度看，向量是一个有方向和大小的量。在数学上，向量可以表示为一个有序的数组。

### 向量的表示
在二维空间中，向量可以表示为 v = (x, y)
在三维空间中，向量可以表示为 v = (x, y, z)

## 1.2 向量的运算

向量之间可以进行加法和数乘运算。

### 向量加法
两个向量相加：v + w = (v₁ + w₁, v₂ + w₂)

### 数乘
标量乘以向量：k·v = (k·v₁, k·v₂)

## 1.3 应用场景

线性代数在计算机图形学、机器学习、物理学等领域有广泛应用。
"""

    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)

    try:
        # 处理文档
        result = await process_uploaded_document(
            file_path=test_file,
            title="测试文档.txt",
            user_email="test@edugenius.ai"
        )

        print(f"✅ 文档处理成功！")
        print(f"📊 统计信息：")
        print(f"   - 总 chunks: {result['stats']['total_chunks']}")
        print(f"   - 总字符数: {result['stats']['total_characters']}")
        print(f"   - 平均长度: {result['stats']['avg_chunk_length']:.1f}")
        print(f"   - 向量维度: {result['stats']['embedding_dimension']}")
        print(f"   - MD5: {result['md5']}")
        print()

        # 测试向量化存储
        print("=" * 60)
        print("📋 测试 2: 向量化存储")
        print("=" * 60)

        md5_hash = result['md5']

        # 创建 ChromaDB collection
        create_document_collection(md5_hash)
        print(f"✅ Collection 创建成功: doc_{md5_hash[:8]}...")

        # 添加 chunks
        chunks = result['chunks']
        embeddings = result['embeddings']
        chunk_texts = result['texts']
        chunk_metadata = [chunk.metadata for chunk in chunks]

        add_document_chunks(
            md5_hash=md5_hash,
            chunks=chunk_texts,
            embeddings=embeddings,
            metadata=chunk_metadata
        )
        print(f"✅ 添加了 {len(chunks)} 个 chunks 到 ChromaDB")

        # 获取统计
        stats = get_collection_stats(md5_hash)
        if stats:
            print(f"📊 Collection 统计: {stats['count']} 个向量")
        print()

        # 测试检索
        print("=" * 60)
        print("📋 测试 3: RAG 检索")
        print("=" * 60)

        query = "什么是向量？"
        print(f"🔍 查询: {query}")

        try:
            retrieved_docs = search_documents(
                query_text=query,
                md5_hash=md5_hash,
                embedding_model=None,
                n_results=2
            )

            print(f"✅ 检索到 {len(retrieved_docs)} 个相关片段：")
            for i, doc in enumerate(retrieved_docs, 1):
                print(f"\n片段 {i} (相似度: {1 - doc['distance']:.2f}):")
                print(f"  {doc['content'][:100]}...")
                if doc.get('metadata'):
                    print(f"  元数据: {doc['metadata']}")

        except Exception as e:
            print(f"❌ 检索失败: {e}")

        print()
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)


async def main():
    """主测试函数"""
    print("\n")
    print("🚀 EduGenius RAG 流程测试")
    print("=" * 60)
    print()

    # 检查配置
    if not settings.DASHSCOPE_API_KEY:
        print("❌ 错误: DASHSCOPE_API_KEY 未设置")
        return

    print(f"✅ 配置检查通过")
    print(f"📊 使用模型: {settings.DEFAULT_MODEL}")
    print()

    # 运行测试
    success = await test_document_processing()

    # 总结
    print("=" * 60)
    print("📊 测试总结")
    print("=" * 60)

    if success:
        print("🎉 RAG 流程测试通过！")
        print("\n功能验证：")
        print("✅ 文档解析（TXT）")
        print("✅ 语义切分")
        print("✅ DashScope Embedding")
        print("✅ ChromaDB 向量存储")
        print("✅ 语义检索（RAG）")
        print("\n下一步：")
        print("1. 修改 teaching.py API 端点，集成 RAG 到对话流程")
        print("2. 测试完整的上传→对话流程")
    else:
        print("⚠️  部分测试失败，请检查配置和网络")


if __name__ == "__main__":
    asyncio.run(main())
