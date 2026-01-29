#!/usr/bin/env python3
"""
测试 PDF 文档处理器修复
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, '/Users/nissoncx/code/EduGenius/api')

from app.services.document_processor import DocumentProcessor
import asyncio

async def test_pdf_processing():
    """测试 PDF 处理功能"""

    # 测试文件路径（如果有的话）
    test_pdf_path = "/Users/nissoncx/code/EduGenius/test_sample.pdf"

    if not os.path.exists(test_pdf_path):
        print("⚠️  测试 PDF 文件不存在")
        print(f"请将测试 PDF 文件放置在: {test_pdf_path}")
        print("\n或者使用以下命令创建测试文件:")
        print("  echo '测试内容' > test.txt")
        return

    print(f"📄 测试 PDF 文件: {test_pdf_path}")
    print("-" * 50)

    try:
        # 创建处理器
        processor = DocumentProcessor()
        print("✅ 文档处理器创建成功")

        # 计算 MD5
        md5_hash = processor.calculate_md5(test_pdf_path)
        print(f"✅ MD5 哈希: {md5_hash}")

        # 处理 PDF
        print("\n🔄 开始处理 PDF...")
        chunks = await processor.process_pdf(
            test_pdf_path,
            metadata={'title': '测试文档'}
        )

        print(f"✅ PDF 处理成功!")
        print(f"   - 生成 {len(chunks)} 个文本块")
        print(f"   - 总字符数: {sum(len(chunk.page_content) for chunk in chunks)}")
        print(f"   - 平均块大小: {sum(len(chunk.page_content) for chunk in chunks) / len(chunks):.0f} 字符")

        # 显示第一个块的内容预览
        if chunks:
            print(f"\n📝 第一个文本块预览:")
            print("-" * 50)
            preview = chunks[0].page_content[:200]
            print(preview + "..." if len(chunks[0].page_content) > 200 else preview)
            print("-" * 50)

        print("\n✅ 所有测试通过!")

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    print("🧪 PDF 文档处理器测试")
    print("=" * 50)
    asyncio.run(test_pdf_processing())
