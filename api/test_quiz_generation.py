#!/usr/bin/env python3
"""
测试题目生成功能

测试内容：
1. Examiner Agent JSON 解析器
2. 各种转义字符场景
3. 实际 LLM 题目生成
"""

import sys
import asyncio
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))


def test_json_parser():
    """测试 JSON 解析器"""
    print("\n" + "="*60)
    print("  测试 JSON 解析器")
    print("="*60 + "\n")

    from app.agents.nodes.examiner import ExaminerAgent

    agent = ExaminerAgent()

    test_cases = [
        {
            "name": "标准 JSON",
            "input": """[
  {
    "question_id": "q1",
    "question": "测试题",
    "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"],
    "correct_answer": "A",
    "explanation": "解析内容",
    "difficulty_level": 3,
    "question_type": "conceptual"
  }
]""",
            "should_pass": True
        },
        {
            "name": "包含转义引号",
            "input": r'''[
  {
    "question_id": "q1",
    "question": "什么是\"变量\"？",
    "options": ["A. \"存储容器\"", "B. 其他选项"],
    "correct_answer": "A",
    "explanation": "变量是\"存储数据\"的容器",
    "difficulty_level": 3,
    "question_type": "conceptual"
  }
]''',
            "should_pass": True
        },
        {
            "name": "包含 LaTeX 公式",
            "input": r'''[
  {
    "question_id": "q1",
    "question": "计算 $\int_0^1 x^2 dx$",
    "options": ["A. $1/3$", "B. $1/2$", "C. $1$", "D. $0$"],
    "correct_answer": "A",
    "explanation": "使用幂函数积分公式：$\int x^n dx = \\frac{x^{n+1}}{n+1} + C$",
    "difficulty_level": 3,
    "question_type": "conceptual"
  }
]''',
            "should_pass": True
        },
        {
            "name": "LLM 响应包裹在 markdown 中",
            "input": '''以下是生成的测试题目：

```json
[
  {
    "question_id": "q1",
    "question": "测试题",
    "options": ["A. 选项A", "B. 选项B"],
    "correct_answer": "A",
    "explanation": "解析",
    "difficulty_level": 3,
    "question_type": "conceptual"
  }
]
```

希望这些题目对你有帮助！''',
            "should_pass": True
        },
        {
            "name": "包含换行符和特殊字符",
            "input": r'''[
  {
    "question_id": "q1",
    "question": "以下哪些是有效的 Python 标识符？\n(多选)",
    "options": ["A. `_var`", "B. `2var`", "C. `var_name`", "D. `class`"],
    "correct_answer": "A",
    "explanation": "Python 标识符不能以数字开头，`class` 是关键字",
    "difficulty_level": 3,
    "question_type": "conceptual"
  }
]''',
            "should_pass": True
        }
    ]

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        print(f"测试 {i}: {test['name']}")

        try:
            result = agent._parse_questions(test['input'])

            if test['should_pass']:
                if result and len(result) > 0:
                    print(f"  ✅ 通过 - 解析出 {len(result)} 道题目")
                    passed += 1
                else:
                    print(f"  ❌ 失败 - 应该解析出题目但返回空")
                    failed += 1
            else:
                if not result or len(result) == 0:
                    print(f"  ✅ 通过 - 正确拒绝无效输入")
                    passed += 1
                else:
                    print(f"  ❌ 失败 - 应该拒绝但解析出了题目")
                    failed += 1

        except Exception as e:
            if test['should_pass']:
                print(f"  ❌ 失败 - 抛出异常: {type(e).__name__}: {e}")
                failed += 1
            else:
                print(f"  ✅ 通过 - 正确抛出异常")
                passed += 1

        print()

    print(f"JSON 解析器测试结果: {passed}/{passed+failed} 通过\n")
    return failed == 0


async def test_llm_generation():
    """测试实际 LLM 题目生成"""
    print("\n" + "="*60)
    print("  测试 LLM 题目生成（需要 API Key）")
    print("="*60 + "\n")

    from app.agents.nodes.examiner import ExaminerAgent
    from app.core.config import settings

    # 检查 API Key
    if not settings.DASHSCOPE_API_KEY or settings.DASHSCOPE_API_KEY == "your_dashscope_api_key_here":
        print("⚠️  未配置 DASHSCOPE_API_KEY，跳过 LLM 生成测试")
        print("   请在 api/.env 中设置有效的 API Key")
        return True

    print(f"✅ API Key 已配置")

    # 创建测试状态
    teaching_state = {
        "student_level": 3,
        "chapter_title": "Python 基础语法",
        "chapter_content": """Python 是一种高级编程语言，具有简洁明了的语法。

变量和数据类型：
- 变量：存储数据的容器，如 x = 10
- 数据类型：整数、浮点数、字符串、布尔值等
- 字符串：用引号括起来的文本，如 "Hello"

运算符：
- 算术运算符：+、-、*、/、//、%、**
- 比较运算符：==、!=、<、>、<=、>=
- 逻辑运算符：and、or、not

控制流：
- if 语句：条件判断
- for 循环：遍历序列
- while 循环：条件循环""",
        "learning_objectives": [
            "理解 Python 变量和数据类型",
            "掌握基本运算符的使用",
            "学会使用条件语句"
        ],
        "wrong_questions": []
    }

    examiner = ExaminerAgent(api_key=settings.DASHSCOPE_API_KEY)

    try:
        print("\n正在调用 LLM 生成题目...")
        print("(这可能需要 10-30 秒)\n")

        questions = await examiner.generate_questions(teaching_state, num_questions=2)

        if questions and len(questions) > 0:
            print(f"✅ 成功生成 {len(questions)} 道题目\n")

            for i, q in enumerate(questions, 1):
                print(f"题目 {i}:")
                print(f"  ID: {q.get('question_id')}")
                print(f"  问题: {q.get('question', '')[:80]}...")
                print(f"  类型: {q.get('question_type')}")
                print(f"  难度: {q.get('difficulty_level')}")
                print(f"  选项数量: {len(q.get('options', []))}")
                print()

            return True
        else:
            print("❌ LLM 返回了空结果")
            return False

    except Exception as e:
        print(f"❌ LLM 生成失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "🧪"*30)
    print("  题目生成功能测试")
    print("🧪"*30 + "\n")

    results = {}

    # 测试 JSON 解析器
    results['json_parser'] = test_json_parser()

    # 测试 LLM 生成
    if len(sys.argv) > 1 and sys.argv[1] == '--with-llm':
        results['llm_generation'] = asyncio.run(test_llm_generation())
    else:
        print("\n⚠️  跳过 LLM 生成测试（使用 --with-llm 参数启用）")

    # 总结
    print("\n" + "="*60)
    print("  测试总结")
    print("="*60 + "\n")

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    for test, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test:20s}: {status}")

    print(f"\n   总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n   🎉 所有测试通过！")
        return 0
    else:
        print(f"\n   ⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
