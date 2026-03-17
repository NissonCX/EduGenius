"""
改进版章节提取器 - 不增加扫描范围，但更聪明地选择

核心改进：
1. 保持扫描范围 60 页（合理）
2. 智能定位"目录"标题页
3. 确保取到连续的完整目录（通常 3-8 页）
4. LLM 提取后验证，如果太少则重试
"""
import re
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings


class ImprovedChapterExtractor:
    """改进版章节提取器"""

    def __init__(self):
        self.api_key = settings.DASHSCOPE_API_KEY
        self.model = "qwen-max"
        self.MAX_SCAN_PAGES = 60  # 保持 60 页，合理范围

    async def extract_chapters_from_text(
        self,
        toc_text: str,
        document_id: int,
        user_id: int,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        直接从目录文本提取章节（不需要页面检测）

        适用场景：
        - 已经有完整的目录文本（如从PDF书签提取）
        - 不需要OCR处理的PDF

        Args:
            toc_text: 完整的目录文本
            document_id: 文档ID
            user_id: 用户ID
            db: 数据库会话

        Returns:
            章节列表
        """
        if not toc_text or len(toc_text) < 100:
            print(f"⚠️  目录文本太短（{len(toc_text)}字符），无法提取章节")
            return []

        print(f"\n{'='*60}")
        print(f"📚 直接从目录文本提取章节")
        print(f"{'='*60}\n")
        print(f"📝 目录文本长度: {len(toc_text)} 字符")

        # 直接调用 LLM 提取
        chapters = await self._llm_extract(toc_text, document_id, user_id, db)

        if chapters:
            print(f"\n   ✅ 提取了 {len(chapters)} 个章节")
            self._print_chapters(chapters)
            return chapters
        else:
            print(f"\n❌ LLM 未能提取章节")
            return []

    async def extract_chapters(
        self,
        ocr_result: Dict[str, Any],
        file_path: str,
        document_id: int,
        user_id: int,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        改进版章节提取

        策略：
        1. 找到"目录"标题页
        2. 从目录页开始，连续取页
        3. LLM 提取
        4. 验证章节数量，太少则重试
        """

        print(f"\n{'='*60}")
        print(f"📚 改进版章节提取")
        print(f"{'='*60}\n")

        if not ocr_result or not ocr_result.get('pages'):
            print(f"❌ 没有 OCR 数据")
            return []

        pages = ocr_result['pages']
        print(f"📄 可用页面：{len(pages)} 页")

        # ========== 第一步：找到目录标题页 ==========
        print(f"\n🔍 第一步：寻找目录标题页...")
        toc_start_page = self._find_toc_title_page(pages)

        if toc_start_page is None:
            print(f"   ⚠️  未找到明确的目录标题，使用评分方法")
            # Fallback：使用评分方法
            toc_pages = self._select_best_pages_by_score(pages, max_pages=8)
        else:
            print(f"   ✅ 找到目录标题：第 {toc_start_page} 页")
            # ========== 第二步：从目录页连续提取 ==========
            print(f"\n📖 第二步：从目录页连续提取...")
            toc_pages = self._extract_continuous_toc_pages(pages, toc_start_page)

            # 🔧 FIX: 如果页面太少或文本太短，扩大范围
            if len(toc_pages) < 3 or len(self._merge_toc_pages(toc_pages)) < 2000:
                print(f"   ⚠️  目录页太少（{len(toc_pages)}）或文本太短，扩大范围...")
                toc_pages = self._expand_toc_pages(pages, toc_start_page, max_pages=15)
                print(f"   ✅ 扩大后：{len(toc_pages)} 个目录页")

        print(f"   ✅ 选择了 {len(toc_pages)} 个目录页：{[p['page_num'] for p in toc_pages]}")

        # ========== 第三步：合并文本 ==========
        toc_text = self._merge_toc_pages(toc_pages)
        print(f"\n📝 第三步：目录文本长度 {len(toc_text)} 字符")

        # ========== 第四步：LLM 提取 ==========
        print(f"\n🧠 第四步：LLM 提取章节...")
        chapters = await self._llm_extract(toc_text, document_id, user_id, db)

        if chapters:
            print(f"\n   ✅ 提取了 {len(chapters)} 个章节")

            # ========== 第五步：验证和重试 ==========
            if len(chapters) < 3:
                print(f"\n⚠️  章节太少（{len(chapters)}），尝试扩大范围...")
                return await self._retry_with_more_pages(pages, document_id, user_id, db)

            self._print_chapters(chapters)
            return chapters
        else:
            print(f"\n❌ LLM 未能提取章节")
            return []

    def _find_toc_title_page(self, pages: List[Dict]) -> Optional[int]:
        """
        找到"目录"标题所在的页面

        匹配模式：
        - "目录"（单独成行）
        - "Contents"（单独成行）
        - "TABLE OF CONTENTS"
        - "目　录"（可能有空格）
        """

        toc_patterns = [
            r'^目录\s*$',  # "目录" 独立成行
            r'^目\s*录\s*$',  # "目　录"
            r'^Contents\s*$',
            r'^TABLE OF CONTENTS\s*$',
            r'^章节目录\s*$',
        ]

        for page in pages:
            text = page.get('text', '')
            page_num = page.get('page_num')

            # 检查前 800 字符（通常标题在前面）
            header = text[:800].strip()

            for pattern in toc_patterns:
                if re.search(pattern, header, re.MULTILINE | re.IGNORECASE):
                    print(f"      → 第 {page_num} 页匹配: {pattern[:20]}")
                    return page_num

        return None

    def _extract_continuous_toc_pages(
        self,
        pages: List[Dict],
        start_page: int
    ) -> List[Dict]:
        """
        从目录标题页开始，连续提取目录页

        策略：
        1. 从目录标题页开始
        2. **目录标题页本身自动包含**（即使内容只是"目录"两个字）
        3. 继续取页，直到连续 3 页不像目录
        4. 最多取 15 页（防止过长）
        """

        # 找到起始页索引
        start_idx = None
        for i, page in enumerate(pages):
            if page['page_num'] == start_page:
                start_idx = i
                break

        if start_idx is None:
            return []

        toc_pages = []
        consecutive_non_toc = 0

        # 🔧 FIX: 从起始页开始，目录标题页本身自动包含
        for i in range(start_idx, min(start_idx + 15, len(pages))):
            page = pages[i]
            text = page.get('text', '')

            # 🔧 FIX: 第一页（目录标题页）自动包含
            is_first_page = (i == start_idx)

            if is_first_page or self._is_likely_toc_page(text):
                toc_pages.append(page)
                consecutive_non_toc = 0
            else:
                consecutive_non_toc += 1
                # 更宽容的连续性检测，允许 3 页不像目录才停止
                if consecutive_non_toc >= 3:
                    break

        return toc_pages

    def _expand_toc_pages(
        self,
        pages: List[Dict],
        start_page: int,
        max_pages: int = 15
    ) -> List[Dict]:
        """扩大目录页选择范围"""

        # 找到起始页索引
        start_idx = None
        for i, page in enumerate(pages):
            if page['page_num'] == start_page:
                start_idx = i
                break

        if start_idx is None:
            return []

        # 从起始页开始，取 max_pages 页（不管是否像目录）
        # 目录可能有特殊格式，不一定是典型的章节页
        end_idx = min(start_idx + max_pages, len(pages))

        return pages[start_idx:end_idx]

    def _is_likely_toc_page(self, text: str) -> bool:
        """
        判断这页是否像目录页

        特征：
        1. 有章节编号（"第X章"、"Chapter X"）
        2. 有页码（"15页"、"P.15"）
        3. 有小节编号（"1.1"、"1.2"）
        4. 章节关键词密度高
        """

        # 快速检查：必须有章节关键词
        has_chapter = (
            '章' in text or 'Chapter' in text or
            re.search(r'\d+\.\d+', text)  # 1.1, 1.2
        )

        if not has_chapter:
            return False

        # 计算目录特征分数
        score = 0

        # 章节编号密度
        chapter_matches = re.findall(r'第[一二三四五六七八九十\d]+章|Chapter\s+\d+', text)
        if len(chapter_matches) >= 3:
            score += 3
        elif len(chapter_matches) >= 1:
            score += 1

        # 小节编号密度
        subsection_matches = re.findall(r'\d+\.\d+', text)
        if len(subsection_matches) >= 5:
            score += 2
        elif len(subsection_matches) >= 2:
            score += 1

        # 页码密度
        page_matches = re.findall(r'\d+\s*[页pP]|P\.\s*\d+', text)
        if len(page_matches) >= 5:
            score += 2
        elif len(page_matches) >= 2:
            score += 1

        # 目录关键词
        if '目录' in text[:200] or 'Contents' in text[:200]:
            score += 3

        return score >= 3

    def _select_best_pages_by_score(
        self,
        pages: List[Dict],
        max_pages: int = 8
    ) -> List[Dict]:
        """
        Fallback：使用评分方法选择最好的页面

        评分标准：
        - 目录关键词：+10 分
        - 章节关键词密度：+3 分/个
        - 页码密度：+2 分
        """

        scored_pages = []

        for page in pages:
            text = page.get('text', '')
            score = 0

            # 目录关键词
            toc_keywords = ['目录', 'Contents', '目　录', 'TABLE OF CONTENTS']
            for keyword in toc_keywords:
                if keyword in text:
                    score += 10
                    # 独立成行额外加分
                    if text.strip().startswith(keyword):
                        score += 5

            # 章节编号
            chapter_count = len(re.findall(r'第[一二三四五六七八九十\d]+章|Chapter\s+\d+', text))
            score += chapter_count * 3

            # 小节编号
            subsection_count = len(re.findall(r'\d+\.\d+', text))
            score += subsection_count * 1

            # 页码
            page_count = len(re.findall(r'\d+\s*[页pP]|P\.\s*\d+', text))
            if page_count > 0:
                density = page_count / len(text) * 1000
                score += min(int(density), 10)

            if score > 0:
                scored_pages.append({
                    'page': page,
                    'score': score
                })

        # 按分数排序
        scored_pages.sort(key=lambda x: x['score'], reverse=True)

        # 取前 N 页
        best_pages = scored_pages[:max_pages]

        return [p['page'] for p in best_pages]

    def _merge_toc_pages(self, pages: List[Dict]) -> str:
        """合并目录页文本"""
        parts = []
        for page in pages:
            page_num = page.get('page_num')
            text = page.get('text', '')
            parts.append(f"--- 第 {page_num} 页 ---\n{text}")

        return "\n\n".join(parts)

    async def _llm_extract(
        self,
        toc_text: str,
        document_id: int,
        user_id: int,
        db: AsyncSession
    ) -> Optional[List[Dict[str, Any]]]:
        """使用 LLM 提取章节"""

        print(f"   📤 发送文本给 LLM（{len(toc_text)} 字符）...")

        # 截断检测：如果文本太长，分批处理
        if len(toc_text) > 6000:
            print(f"   ⚠️  文本较长（{len(toc_text)} 字符），可能被截断")
            # 考虑分批处理或使用更长的上下文模型

        import httpx

        prompt = f"""你是一个专业的教材目录识别专家。请从下面的文本中提取教材的目录结构。

【关键要求】：
1. **必须提取所有章节**，不要因为章节多就停止
2. **必须提取所有小节和子小节**（1.1、1.1.1 等）
3. 如果目录在多个页面，要全部提取
4. 注意：不要漏掉中间的任何章节

【输出格式】（严格按照 JSON 格式）：
{{
  "has_toc": true,
  "confidence": "high",
  "total_chapters": 章节总数（整数）,
  "chapters": [
    {{
      "chapter_number": 1,
      "chapter_title": "章节标题（不包含"第X章"）",
      "page_number": 起始页码,
      "subsections": [
        {{"subsection_number": "1.1", "subsection_title": "小节标题", "page_number": 页码}},
        {{"subsection_number": "1.2", "subsection_title": "小节标题", "page_number": 页码}}
      ]
    }}
  ]
}}

【目录文本】：
```
{toc_text[:6000]}
```

【注意】：
- 如果上面被截断了（文本在章节中间断开），回复 "TRUNCATED"，我会提供完整文本
- 必须提取完整，不要遗漏任何章节
"""

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
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
                        "temperature": 0.0,  # 降低温度，提高一致性
                        "max_tokens": 8000
                    }
                )

            if response.status_code != 200:
                print(f"   ❌ LLM 调用失败：{response.status_code}")
                return None

            result = response.json()
            content = result['choices'][0]['message']['content']

            print(f"   📥 LLM 返回内容长度: {len(content)} 字符")
            print(f"   📥 LLM 返回内容预览:\n{content[:1500]}...\n")

            # 检查是否被截断
            if "TRUNCATED" in content or "truncated" in content:
                print(f"   ⚠️  LLM 报告文本被截断，自动重试...")
                # 自动使用重试机制
                return None  # 让上层调用 _retry_with_more_pages

            # 🔧 FIX: 改进 JSON 解析 - 尝试多种模式
            json_str = None

            # 模式1: 标准 markdown JSON 代码块
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
            if json_match:
                json_str = json_match.group(1)
                print(f"   ✅ 使用模式1匹配：标准 markdown JSON")
            else:
                # 模式2: 简单代码块
                json_match = re.search(r'```\s*([\s\S]*?)\s*```', content)
                if json_match:
                    json_str = json_match.group(1)
                    print(f"   ✅ 使用模式2匹配：简单代码块")
                else:
                    # 模式3: 直接查找 JSON 对象（从头到尾）
                    json_match = re.search(r'\{[\s\S]*\}', content)
                    if json_match:
                        json_str = json_match.group()
                        print(f"   ✅ 使用模式3匹配：纯 JSON 对象")
                    else:
                        print(f"   ❌ 所有 JSON 匹配模式都失败")
                        print(f"   📄 原始内容:\n{content[:500]}...")
                        return None

            if not json_str:
                print(f"   ❌ 未能提取 JSON 字符串")
                return None

            print(f"   🔍 提取的 JSON 长度: {len(json_str)} 字符")

            # 解析 JSON
            try:
                data = json.loads(json_str)
                print(f"   ✅ JSON 解析成功")
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON 解析失败: {e}")
                print(f"   📄 JSON 字符串:\n{json_str[:1000]}...")
                # 尝试修复常见的 JSON 问题
                try:
                    # 尝试移除末尾的逗号
                    fixed_json = re.sub(r',\s*([}\]])', r'\1', json_str)
                    data = json.loads(fixed_json)
                    print(f"   ✅ JSON 修复后解析成功")
                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON 修复后仍然解析失败: {e}")
                    return None

            if not data.get('has_toc'):
                print(f"   ⚠️  LLM 认为没有目录 (has_toc = false)")
                return None

            chapters = data.get('chapters', [])
            if not chapters:
                print(f"   ⚠️  LLM 返回了空章节列表")
                return None

            # 创建数据库记录
            for chapter_info in chapters:
                await self._create_chapter_progress(
                    db, document_id, user_id, chapter_info
                )

            return chapters

        except json.JSONDecodeError as e:
            print(f"   ❌ JSON 解析失败: {e}")
            print(f"   📄 LLM 响应：{content[:300]}...")
            return None
        except Exception as e:
            print(f"   ❌ LLM 提取失败: {e}")
            return None

    async def _retry_with_more_pages(
        self,
        pages: List[Dict],
        document_id: int,
        user_id: int,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """重试：使用更多页面"""

        print(f"   🔄 重试：使用所有 {len(pages)} 页")

        # 使用所有页面
        toc_text = self._merge_toc_pages(pages)

        chapters = await self._llm_extract(toc_text, document_id, user_id, db)

        if chapters and len(chapters) >= 3:
            print(f"   ✅ 重试成功：提取了 {len(chapters)} 章")
            return chapters
        else:
            print(f"   ❌ 重试失败")
            return []

    async def _create_chapter_progress(
        self,
        db: AsyncSession,
        document_id: int,
        user_id: int,
        chapter_info: Dict[str, Any]
    ):
        """创建章节进度记录和小节记录"""
        from app.models.document import Progress
        from sqlalchemy import select, text

        print(f"\n{'='*60}")
        print(f"💾 创建章节进度记录 (ImprovedChapterExtractor)")
        print(f"{'='*60}")
        print(f"📋 chapter_info 内容: {chapter_info}")
        print(f"📋 chapter_number: {chapter_info.get('chapter_number', 'N/A')}")
        print(f"📋 chapter_title: {chapter_info.get('chapter_title', 'N/A')}")
        print(f"{'='*60}\n")

        # 检查是否已存在
        existing = await db.execute(
            select(Progress).where(
                Progress.document_id == document_id,
                Progress.chapter_number == chapter_info.get('chapter_number', 1)
            )
        )
        if existing.scalar_one_or_none():
            print(f"   ℹ️  章节 {chapter_info.get('chapter_number')} 已存在，跳过创建")
            return

        progress = Progress(
            document_id=document_id,
            user_id=user_id,
            chapter_number=chapter_info.get('chapter_number', 1),
            chapter_title=chapter_info.get('chapter_title', '未命名章节'),
            completion_percentage=0.0,
            time_spent_minutes=0,
            is_locked=True
        )

        db.add(progress)
        await db.commit()

        print(f"✅ 章节记录创建成功:")
        print(f"   - 章节: {progress.chapter_number}")
        print(f"   - 标题: {progress.chapter_title}")
        print(f"   - ID: {progress.id}")

        # 🔧 NEW: 保存小节到数据库
        subsections = chapter_info.get('subsections', [])
        if subsections:
            print(f"\n💾 保存 {len(subsections)} 个小节到数据库...")

            for subsection_info in subsections:
                try:
                    insert_stmt = text("""
                        INSERT INTO subsections
                        (user_id, document_id, chapter_number, subsection_number,
                         subsection_title, page_number, cognitive_level_assigned,
                         completion_percentage, time_spent_minutes)
                        VALUES (:user_id, :document_id, :chapter_number, :subsection_number,
                                :subsection_title, :page_number, :cognitive_level,
                                :completion_percentage, :time_spent_minutes)
                        ON CONFLICT(user_id, document_id, chapter_number, subsection_number)
                        DO UPDATE SET
                            subsection_title = :subsection_title,
                            page_number = :page_number
                    """)

                    await db.execute(insert_stmt, {
                        "user_id": user_id,
                        "document_id": document_id,
                        "chapter_number": chapter_info.get('chapter_number', 1),
                        "subsection_number": subsection_info.get('subsection_number', ''),
                        "subsection_title": subsection_info.get('subsection_title', ''),
                        "page_number": subsection_info.get('page_number'),
                        "cognitive_level": 3,
                        "completion_percentage": 0.0,
                        "time_spent_minutes": 0.0
                    })

                except Exception as e:
                    print(f"   ⚠️  小节 {subsection_info.get('subsection_number')} 保存失败: {e}")

            await db.commit()
            print(f"✅ 小节保存完成")

    def _print_chapters(self, chapters: List[Dict[str, Any]]):
        """打印章节信息"""
        print(f"\n   📚 提取的章节：")
        for ch in chapters:
            subs = ch.get('subsections', [])
            print(f"      第 {ch['chapter_number']} 章：{ch['chapter_title']}")
            print(f"         小节：{len(subs)} 个")
            for sub in subs[:5]:  # 只打印前 5 个小节
                print(f"           - {sub.get('subsection_number')} {sub.get('subsection_title')}")
            if len(subs) > 5:
                print(f"           ... 还有 {len(subs) - 5} 个小节")
