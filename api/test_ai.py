#!/usr/bin/env python3
"""
EduGenius AI 连接测试脚本
测试 DashScope API 是否可用，验证流式响应
"""
import asyncio
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langchain_community.chat_models.tongyi import ChatTongyi
from app.core.config import settings


async def test_basic_chat():
    """测试基础对话功能"""
    print("=" * 60)
    print("📋 测试 1: 基础对话功能")
    print("=" * 60)

    try:
        # 初始化 LLM
        llm = ChatTongyi(
            dashscope_api_key=settings.DASHSCOPE_API_KEY,
            model_name=settings.DEFAULT_MODEL,
            temperature=0.7
        )

        # 测试对话
        response = await llm.ainvoke([
            {"role": "system", "content": "你是一位专业的AI导师。"},
            {"role": "user", "content": "请用一句话解释什么是机器学习？"}
        ])

        print(f"✅ 基础对话成功！")
        print(f"📝 回复: {response.content[:100]}...")
        print()
        return True

    except Exception as e:
        print(f"❌ 基础对话失败: {str(e)}")
        print()
        return False


async def test_streaming():
    """测试流式响应"""
    print("=" * 60)
    print("📋 测试 2: 流式响应功能")
    print("=" * 60)

    try:
        llm = ChatTongyi(
            dashscope_api_key=settings.DASHSCOPE_API_KEY,
            model_name=settings.DEFAULT_MODEL,
            temperature=0.7
        )

        print("🔄 正在测试流式输出...")
        print("   (逐字打印效果)")

        # 测试流式响应
        full_response = ""
        async for chunk in llm.astream([
            {"role": "system", "content": "你是一位专业的AI导师。"},
            {"role": "user", "content": "用50字以内解释什么是向量？"}
        ]):
            content = chunk.content
            if content:
                print(content, end="", flush=True)
                full_response += content

        print("\n")
        print(f"✅ 流式响应成功！")
        print(f"📝 总字符数: {len(full_response)}")
        print()
        return True

    except Exception as e:
        print(f"❌ 流式响应失败: {str(e)}")
        print()
        return False


async def test_tutor_agent():
    """测试 Tutor 智能体"""
    print("=" * 60)
    print("📋 测试 3: Tutor 智能体集成")
    print("=" * 60)

    try:
        from app.agents.nodes.tutor import TutorAgent
        from app.agents.state.teaching_state import TeachingState

        # 创建测试状态
        test_state = TeachingState(
            student_level=3,
            chapter_title="线性代数基础",
            chapter_content="向量是线性代数的基本概念...",
            conversation_history=[],
            correct_questions=[],
            wrong_questions=[],
            quiz_attempts=0,
            success_rate=0.0
        )

        # 初始化 Tutor
        tutor = TutorAgent()
        print("🎓 Tutor 智能体初始化成功")

        # 测试讲解功能
        explanation = await tutor.explain_concept(
            state=test_state,
            topic="向量的定义"
        )

        print(f"✅ Tutor 讲解成功！")
        print(f"📝 讲解内容（前150字）: {explanation[:150]}...")
        print()
        return True

    except Exception as e:
        print(f"❌ Tutor 智能体测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        print()
        return False


async def main():
    """主测试函数"""
    print("\n")
    print("🚀 EduGenius AI 连接测试")
    print("=" * 60)
    print()

    # 检查配置
    if not settings.DASHSCOPE_API_KEY:
        print("❌ 错误: DASHSCOPE_API_KEY 未设置")
        print("请在 api/.env 文件中设置 DASHSCOPE_API_KEY")
        print("获取地址: https://dashscope.console.aliyun.com/apiKey")
        return

    print(f"✅ 配置检查通过")
    print(f"📊 使用模型: {settings.DEFAULT_MODEL}")
    print(f"🔑 API Key: {'*' * 20}{settings.DASHSCOPE_API_KEY[-4:]}")
    print()

    # 运行测试
    results = []

    # 测试 1: 基础对话
    results.append(await test_basic_chat())

    # 测试 2: 流式响应
    results.append(await test_streaming())

    # 测试 3: Tutor 智能体
    results.append(await test_tutor_agent())

    # 总结
    print("=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    print(f"✅ 通过: {sum(results)}/{len(results)}")
    print(f"❌ 失败: {len(results) - sum(results)}/{len(results)}")

    if all(results):
        print("\n🎉 所有测试通过！DashScope 集成成功！")
        print("\n下一步:")
        print("1. 启动后端服务: cd api && python -m uvicorn main:app --reload")
        print("2. 前端连接真实 API")
    else:
        print("\n⚠️  部分测试失败，请检查配置和网络连接")


if __name__ == "__main__":
    asyncio.run(main())
