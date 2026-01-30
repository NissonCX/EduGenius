"""
增强版章节划分服务 - 正确解析教科书目录

改进点：
1. 接收纯净的目录文本（不含页面标记）
2. 使用更精准的 LLM prompt
3. 多层次验证和 fallback 机制
"""
import json
import re
from typing import List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, Progress
from app.core.config import settings


class EnhancedChapterDivider:
    """增强版章节划分器"""

    def __init__(self):
        self.api_key = settings.DASHSCOPE_API_KEY
        self.model = "qwen-max"  # 使用更强的模型

    async def divide_document_into_chapters(
        self,
        document_id: int,
        user_id: int,
        document_text: str,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        根据文档文本划分章节

        Args:
            document_id: 文档 ID
            user_id: 用户 ID
            document_text: 完整文档文本（包含目录）
            db: 数据库会话

        Returns:
            章节列表
        """
        print(f"\n{'='*60}")
        print(f"📚 开始处理文档 {document_id} 的章节划分")
        print(f"{'='*60}\n")

        # 使用增强版提示词
        result = await self._extract_toc_with_llm(document_text)

        if result.get('has_toc', False):
            chapters = result.get('chapters', [])
            print(f"\n✅ LLM成功提取 {len(chapters)} 个章节:")
            for ch in chapters:
                subs = ch.get('subsections', [])
                print(f"   第{ch['chapter_number']}章: {ch['chapter_title']} ({len(subs)}个小节)")
            print()

            # 创建学习进度记录
            for chapter_info in chapters:
                await self._create_chapter_progress(
                    db, document_id, user_id, chapter_info
                )

            return chapters
        else:
            print("\n⚠️  未找到目录，使用启发式方法\n")
            return await self._heuristic_division_with_fallback(
                db, document_id, user_id, document_text
            )

    async def _extract_toc_with_llm(
        self,
        document_text: str
    ) -> Dict[str, Any]:
        """
        使用 LLM 提取目录结构

        重点改进：
        1. 更清晰的 prompt
        2. 提供更多示例
        3. 要求 LLM 确认是否找到目录
        """
        # 增加提取的文本长度，确保包含所有章节
        # 对于目录较长的教材，可能需要更多文本
        # 🔧 FIX: 使用完整的文本而不是截断到30000字符
        toc_section = document_text  # 使用完整文本

        print("📝 正在发送给 LLM 分析目录...")
        print(f"📄 分析文本长度: {len(toc_section)} 字符")
        print(f"📄 原始文本长度: {len(document_text)} 字符")
        if len(toc_section) < len(document_text):
            print(f"⚠️  文本被截断！只使用了 {len(toc_section)}/{len(document_text)} 字符")

        # 打印文本预览用于调试
        print(f"📖 文本预览:\n{toc_section[:500]}...")
        print()

        prompt = f"""你是一个专业的教材目录识别专家。请从下面的文本中提取教材的目录结构。

【重要要求】：
1. 仔细查找目录部分，通常在文档开头，会有"目录"、"Contents"等标题
2. 目录包含章节编号和标题，可能有页码
3. **关键：必须提取文本中出现的所有章节，不要遗漏任何章节**
4. 请提取所有章节和小节信息
5. 对于中文教材，特别注意"第一章"、"第二章"或"第1章"、"第2章"这样的格式

【文本内容】：
```
{toc_section}
```

【示例 - 如何提取】：

示例1 - 中文教材：
输入：
```
目录
第一章  物质及其变化
  第一节  物质的分类及转化        2
  第二节  离子反应                10
  第三节  氧化还原反应            18
第二章  海水中的重要元素
  第一节  钠及其化合物            28
  第二节  氯及其化合物            36
```
输出：
{{
  "has_toc": true,
  "confidence": "high",
  "total_chapters": 2,
  "chapters": [
    {{
      "chapter_number": 1,
      "chapter_title": "物质及其变化",
      "page_number": 2,
      "subsections": [
        {{"subsection_number": "1.1", "subsection_title": "物质的分类及转化", "page_number": 2}},
        {{"subsection_number": "1.2", "subsection_title": "离子反应", "page_number": 10}},
        {{"subsection_number": "1.3", "subsection_title": "氧化还原反应", "page_number": 18}}
      ]
    }},
    {{
      "chapter_number": 2,
      "chapter_title": "海水中的重要元素",
      "page_number": 28,
      "subsections": [
        {{"subsection_number": "2.1", "subsection_title": "钠及其化合物", "page_number": 28}},
        {{"subsection_number": "2.2", "subsection_title": "氯及其化合物", "page_number": 36}}
      ]
    }}
  ]
}}

【提取规则】：
1. 章节编号格式：
   - 中文数字：第一章、第二章、第三章
   - 阿拉伯数字：第1章、第2章
   - 英文格式：Chapter 1、Chapter 2
   - 点序号：1.、2.、3.

2. 小节编号格式：
   - 点序号：1.1、1.2、2.1、2.2
   - 中文：第一节、第二节

3. 清理标题：
   - 移除章节编号（如"第一章"）
   - 移除页码（如"    2"或"P.2"）
   - 只保留纯文本标题

【返回格式】（严格按照 JSON 格式，不要包含其他文字）：
{{
  "has_toc": true 或 false,
  "confidence": "high" 或 "medium" 或 "low",
  "total_chapters": 章节总数（整数）,
  "chapters": [
    {{
      "chapter_number": 1,
      "chapter_title": "章节标题（不包含章节号和页码）",
      "page_number": 页码数字,
      "subsections": [
        {{
          "subsection_number": "1.1",
          "subsection_title": "小节标题（不包含小节号和页码）",
          "page_number": 页码数字
        }}
      ]
    }}
  ]
}}

【判断标准】：
- 如果找到清晰的章节标题（有明确的章节编号和标题），设置 has_toc = true
- 如果完全没有目录结构或无法识别章节，设置 has_toc = false
- confidence 表示你的置信度：high（非常确定）、medium（基本确定）、low（不太确定）
"""

        try:
            # 🔧 FIX: 改用 OpenAI 兼容的 API（更可靠）
            import httpx

            print(f"🔑 使用模型: {self.model}")
            print(f"📡 调用 DashScope OpenAI 兼容 API...")

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "你是专业的教材目录识别专家。"},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.0,
                        "max_tokens": 8000
                    }
                )

                print(f"📊 API响应状态: {response.status_code}")

                if response.status_code != 200:
                    print(f"❌ LLM API 错误: {response.status_code}")
                    print(f"📦 错误详情: {response.text[:500]}")
                    return {"has_toc": False}

                result = response.json()
                content = result['choices'][0]['message']['content']

                if not content or not content.strip():
                    print("⚠️  LLM 返回了空响应")
                    return {"has_toc": False}

                content = content.strip()
                print(f"📥 LLM 返回内容长度: {len(content)} 字符")
                print(f"📥 LLM 返回内容预览:\n{content[:1500]}...\n")

                # 🔧 FIX: 改进 JSON 解析 - 尝试多种模式
                json_str = None

                # 模式1: 标准 markdown JSON 代码块
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
                if json_match:
                    json_str = json_match.group(1)
                    print("✅ 使用模式1匹配：标准 markdown JSON")
                else:
                    # 模式2: 简单代码块
                    json_match = re.search(r'```\s*([\s\S]*?)\s*```', content)
                    if json_match:
                        json_str = json_match.group(1)
                        print("✅ 使用模式2匹配：简单代码块")
                    else:
                        # 模式3: 直接查找 JSON 对象（从头到尾）
                        json_match = re.search(r'\{[\s\S]*\}', content)
                        if json_match:
                            json_str = json_match.group()
                            print("✅ 使用模式3匹配：纯 JSON 对象")
                        else:
                            print("❌ 所有 JSON 匹配模式都失败")
                            print(f"📄 原始内容:\n{content}")
                            return {"has_toc": False}

                if not json_str:
                    print("❌ 未能提取 JSON 字符串")
                    return {"has_toc": False}

                print(f"🔍 提取的 JSON 长度: {len(json_str)} 字符")
                print(f"🔍 JSON 预览:\n{json_str[:500]}...")

                # 解析 JSON
                try:
                    parsed_result = json.loads(json_str)
                    print("✅ JSON 解析成功")
                except json.JSONDecodeError as e:
                    print(f"❌ JSON 解析失败: {e}")
                    print(f"📄 JSON 字符串:\n{json_str[:1000]}...")
                    # 尝试修复常见的 JSON 问题
                    try:
                        # 尝试移除末尾的逗号
                        fixed_json = re.sub(r',\s*([}\]])', r'\1', json_str)
                        parsed_result = json.loads(fixed_json)
                        print("✅ JSON 修复后解析成功")
                    except:
                        return {"has_toc": False}

                # 验证结果
                if not parsed_result.get('has_toc'):
                    print("⚠️  LLM 认为没有目录 (has_toc = false)")
                    return {"has_toc": False}

                chapters = parsed_result.get('chapters', [])
                if not chapters:
                    print("⚠️  LLM 返回了空章节列表")
                    return {"has_toc": False}

                print(f"✅ LLM 识别成功，共 {len(chapters)} 章:")
                for ch in chapters:
                    subs = ch.get('subsections', [])
                    print(f"   第{ch.get('chapter_number', 'N/A')}章: {ch.get('chapter_title', 'N/A')}")
                    if subs:
                        print(f"      小节数: {len(subs)}")
                        for sub in subs[:3]:
                            print(f"        - {sub.get('subsection_number', '')} {sub.get('subsection_title', '')}")
                        if len(subs) > 3:
                            print(f"        ... 共 {len(subs)} 个小节")

                return parsed_result

        except httpx.TimeoutException:
            print("❌ LLM API 调用超时")
            return {"has_toc": False}
        except httpx.RequestError as e:
            print(f"❌ LLM API 网络错误: {e}")
            return {"has_toc": False}
        except Exception as e:
            print(f"❌ LLM 调用失败: {e}")
            import traceback
            traceback.print_exc()
            return {"has_toc": False}

    async def _heuristic_division_with_fallback(
        self,
        db: AsyncSession,
        document_id: int,
        user_id: int,
        document_text: str
    ) -> List[Dict[str, Any]]:
        """启发式章节划分（改进版 - 识别所有章节）"""
        print("🔍 使用启发式方法识别章节...")

        # 🔧 FIX: 使用完整文本而不是截断
        search_text = document_text

        print(f"📄 搜索文本长度: {len(search_text)} 字符")

        # 改进的正则模式，更准确匹配章节标题
        patterns = [
            # 中文章节（最常见）- 第一章 物质及其变化
            # 使用非贪婪匹配，避免匹配过多内容
            {
                'pattern': r'第([一二三四五六七八九十百]+)\s*章[：:\s]*([^\n]{2,100}?)(?=\n第|\n\s*第|\n\s*\d+\.|\n\n|$)',
                'type': 'chinese_chapter',
                'converter': lambda x: self._chinese_to_number(x)
            },
            # 数字章节 - 第1章 物质及其变化
            {
                'pattern': r'第(\d+)\s*章[：:\s]*([^\n]{2,100}?)(?=\n第|\n\s*第|\n\s*\d+\.|\n\n|$)',
                'type': 'number_chapter',
                'converter': lambda x: int(x)
            },
            # 英文章节 - Chapter 1 Matter and Its Changes
            {
                'pattern': r'Chapter\s+(\d+)\s*[:：]?\s*([^\n]{5,100}?)(?=\s+Chapter|\n\n|$)',
                'type': 'english_chapter',
                'converter': lambda x: int(x)
            },
            # 点序号章节 - 1. 物质及其变化
            {
                'pattern': r'^\s*(\d+)\.\s+([^\n]{5,100}?)(?=\s+\d+\.\s|\n\n|$)',
                'type': 'dot_number',
                'converter': lambda x: int(x)
            },
        ]

        # 尝试每种模式
        for pattern_info in patterns:
            pattern = pattern_info['pattern']
            converter = pattern_info['converter']

            matches = list(re.finditer(pattern, search_text, re.MULTILINE))

            if not matches:
                print(f"⚠️ '{pattern_info['type']}' 模式未找到匹配")
                continue

            chapters = []
            seen_titles = set()  # 用于去重

            for match in matches:
                try:
                    chapter_num = converter(match.group(1))  # 提取章节号
                    chapter_title = match.group(2).strip()   # 提取章节标题

                    # 清理标题：移除页码、多余空格、特殊字符
                    chapter_title = re.sub(r'\s*\d+\s*$', '', chapter_title)  # 移除末尾页码
                    chapter_title = re.sub(r'\s+', ' ', chapter_title)  # 规范空格
                    chapter_title = chapter_title.strip()

                    # 过滤：标题不能太短，且不能重复
                    if chapter_title and len(chapter_title) > 2:
                        # 使用章节号和标题的组合作为唯一标识
                        title_key = f"{chapter_num}_{chapter_title}"
                        if title_key not in seen_titles:
                            seen_titles.add(title_key)
                            chapters.append({
                                'chapter_number': chapter_num,
                                'chapter_title': chapter_title,
                                'page_number': 1  # 默认页码
                            })
                except Exception as e:
                    print(f"   ⚠️  处理匹配项失败: {e}")
                    continue

            if chapters and len(chapters) >= 1:
                print(f"✅ 使用 '{pattern_info['type']}' 模式找到 {len(chapters)} 章:")
                for ch in chapters:
                    print(f"   第{ch['chapter_number']}章: {ch['chapter_title']}")

                # 为每个章节尝试识别小节
                for chapter_info in chapters:
                    # 尝试从搜索文本中提取该章节的小节
                    subsections = self._extract_subsections_for_chapter(
                        search_text,
                        chapter_info['chapter_number']
                    )

                    if subsections:
                        chapter_info['subsections'] = subsections
                        print(f"      💾 第{chapter_info['chapter_number']}章识别到 {len(subsections)} 个小节")

                    # 创建进度记录（包括小节）
                    await self._create_chapter_progress(
                        db, document_id, user_id, chapter_info
                    )

                return chapters
            else:
                print(f"⚠️ '{pattern_info['type']}' 模式未找到足够的章节")

        # 最后的 fallback：创建单个默认章节
        print("⚠️  无法识别章节，创建默认章节")

        # 尝试从数据库获取文档标题
        from app.models.document import Document
        doc_result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = doc_result.scalar_one_or_none()
        doc_title = document.title if document else "完整教材"

        default_chapter = {
            'chapter_number': 1,
            'chapter_title': doc_title,  # 使用文档标题而不是"默认章节"
            'page_number': 1
        }
        await self._create_chapter_progress(
            db, document_id, user_id, default_chapter
        )

        return [default_chapter]

    async def _create_chapter_progress(
        self,
        db: AsyncSession,
        document_id: int,
        user_id: int,
        chapter_info: Dict[str, Any]
    ):
        """创建章节学习进度记录（包括小节）"""
        try:
            print(f"\n{'='*60}")
            print(f"💾 创建章节进度记录")
            print(f"{'='*60}")
            print(f"📋 chapter_info 内容: {chapter_info}")
            print(f"📋 chapter_number: {chapter_info.get('chapter_number', 'N/A')}")
            print(f"📋 chapter_title: {chapter_info.get('chapter_title', 'N/A')}")
            print(f"📋 page_number: {chapter_info.get('page_number', 'N/A')}")
            print(f"{'='*60}\n")

            # 获取用户的认知等级
            from app.models.document import User
            from app.models.subsection import Subsection
            user_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            cognitive_level = user.cognitive_level if user else 3

            # 创建章节进度记录
            progress = Progress(
                user_id=user_id,
                document_id=document_id,
                chapter_number=chapter_info.get('chapter_number', 1),
                chapter_title=chapter_info.get('chapter_title', '未命名章节'),
                cognitive_level_assigned=cognitive_level,
                completion_percentage=0,
                time_spent_minutes=0
            )

            db.add(progress)
            await db.commit()

            print(f"✅ 章节记录创建成功:")
            print(f"   - 章节: {progress.chapter_number}")
            print(f"   - 标题: {progress.chapter_title}")
            print(f"   - ID: {progress.id}")

            # 如果有小节信息，也创建小节记录
            subsections = chapter_info.get('subsections', [])
            if subsections:
                print(f"\n   💾 开始创建 {len(subsections)} 个小节记录...")
                from sqlalchemy import text
                success_count = 0
                for idx, subsection_info in enumerate(subsections, 1):
                    try:
                        # 使用executemany批量插入，避免参数格式问题
                        insert_stmt = text("""
                            INSERT INTO subsections
                            (user_id, document_id, chapter_number, subsection_number,
                             subsection_title, page_number, cognitive_level_assigned,
                             completion_percentage, time_spent_minutes)
                            VALUES (:user_id, :document_id, :chapter_number, :subsection_number,
                                    :subsection_title, :page_number, :cognitive_level,
                                    :completion_pct, :time_spent)
                        """)

                        subsection_number = subsection_info.get('subsection_number', '')
                        subsection_title = subsection_info.get('subsection_title', '')

                        await db.execute(insert_stmt, {
                            'user_id': user_id,
                            'document_id': document_id,
                            'chapter_number': chapter_info.get('chapter_number', 1),
                            'subsection_number': subsection_number,
                            'subsection_title': subsection_title,
                            'page_number': subsection_info.get('page_number', 1),
                            'cognitive_level': cognitive_level,
                            'completion_pct': 0.0,
                            'time_spent': 0.0
                        })
                        success_count += 1
                        print(f"      ✅ [{idx}/{len(subsections)}] 小节 {subsection_number}: {subsection_title}")
                    except Exception as e:
                        print(f"      ⚠️  [{idx}/{len(subsections)}] 创建小节失败: {e}")
                        import traceback
                        traceback.print_exc()
                        continue

                await db.commit()
                print(f"\n   ✅ 小节创建完成: {success_count}/{len(subsections)} 成功")
            else:
                print(f"   ℹ️  此章节没有小节信息")

        except Exception as e:
            print(f"❌ 创建章节进度失败: {e}")
            import traceback
            traceback.print_exc()

    def _extract_subsections_for_chapter(
        self,
        search_text: str,
        chapter_number: int
    ) -> List[Dict[str, Any]]:
        """为指定章节提取小节"""
        subsections = []

        # 定义小节匹配模式
        subsection_patterns = [
            # 数字小节：1.1、1.2 等
            rf'{chapter_number}\.(\d+)\s*[.、:：]?\s*([^\n]{{2,80}}?)(?=\n{chapter_number}\.|\n\n|\n第|\Z)',
            # 中文小节：第一节、第二节等
            rf'第[一二三四五六七八九十]+\s*节\s*[.、:：]?\s*([^\n]{{2,80}}?)(?=\n第|\n\n|\Z)',
        ]

        import re
        for pattern in subsection_patterns:
            matches = re.finditer(pattern, search_text, re.MULTILINE)
            for match in matches:
                try:
                    if chapter_number == int(match.group(1)):  # 确保是当前章节的小节
                        subsection_title = match.group(2).strip()
                        subsection_title = re.sub(r'\s*\d+\s*$', '', subsection_title)  # 移除页码
                        subsection_title = re.sub(r'\s+', ' ', subsection_title)

                        if subsection_title and len(subsection_title) > 2:
                            subsection_num = match.group(1)
                            subsections.append({
                                'subsection_number': f"{chapter_number}.{subsection_num}",
                                'subsection_title': subsection_title,
                                'page_number': 1
                            })
                except (ValueError, IndexError):
                    continue

            if subsections:
                break  # 如果找到小节，停止尝试其他模式

        return subsections

    def _chinese_to_number(self, chinese_num: str) -> int:
        """将中文数字转换为阿拉伯数字"""
        chinese_map = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
            '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15,
            '十六': 16, '十七': 17, '十八': 18, '十九': 19, '二十': 20
        }

        # 处理"二十一"到"九十九"
        if chinese_num in chinese_map:
            return chinese_map[chinese_num]

        # 简单处理：提取数字部分
        match = re.search(r'\d+', chinese_num)
        if match:
            return int(match.group(0))

        return 1


# 导出函数
async def process_document_v2(
    file_path: str,
    title: str,
    user_email: str
) -> Dict[str, Any]:
    """处理文档（v2）"""
    processor = EnhancedDocumentProcessor()

    md5_hash = processor.calculate_md5(file_path)

    metadata = {
        'title': title,
        'user_email': user_email,
        'md5': md5_hash
    }

    # 处理 PDF
    result = await processor.process_pdf_v2(file_path, metadata)

    result['md5'] = md5_hash
    return result
