"""
测试小节提取功能
"""
import asyncio
from app.services.chapter_divider import ChapterDivider


async def test_subsection_extraction():
    """测试目录提取（包含小节）"""
    
    # 模拟包含小节的目录
    sample_toc = """
    目录
    
    第一章 线性代数基础 ........................... 1
        1.1 向量的定义 ........................... 2
        1.2 向量的运算 ........................... 8
        1.3 向量空间 ............................. 15
        1.4 线性相关性 ........................... 22
    
    第二章 矩阵理论 ............................... 30
        2.1 矩阵的定义 ........................... 31
        2.2 矩阵的运算 ........................... 38
        2.3 矩阵的秩 ............................. 45
    
    第三章 微积分入门 ............................. 52
        3.1 极限的概念 ........................... 53
        3.2 导数的定义 ........................... 60
        3.3 积分的应用 ........................... 68
    """
    
    divider = ChapterDivider()
    
    print("📚 开始测试小节提取...")
    print("=" * 60)
    
    result = await divider.extract_table_of_contents(
        document_text=sample_toc,
        document_title="高等数学教程"
    )
    
    print(f"\n✅ 提取结果：")
    print(f"   - 是否找到目录：{result.get('has_toc')}")
    print(f"   - 章节总数：{result.get('total_chapters')}")
    print()
    
    for chapter in result.get('chapters', []):
        print(f"📖 第{chapter['chapter_number']}章：{chapter['chapter_title']}")
        
        subsections = chapter.get('subsections', [])
        if subsections:
            print(f"   包含 {len(subsections)} 个小节：")
            for subsection in subsections:
                print(f"      {chapter['chapter_number']}.{subsection['subsection_number']} {subsection['subsection_title']}")
        else:
            print(f"   （无小节）")
        print()
    
    print("=" * 60)
    print("✅ 测试完成！")


if __name__ == "__main__":
    asyncio.run(test_subsection_extraction())
