"""
智能章节提取器 - 多策略、多层次提取目录

核心改进：
1. 扩大搜索范围：扫描前 150 页（而不是 60）
2. 智能目录定位：找到"目录"标题页
3. 连续性检测：目录通常是连续的几页
4. 数量验证：章节数量应该合理（3-20章）
5. 二次提取：如果第一次提取太少，尝试更多页面
"""
import re
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings


class SmartChapterExtractor:
    """智能章节提取器"""

    def __init__(self):
        self.api_key = settings.DASHSCOPE_API_KEY
        self.model = "qwen-max"

        # 扩展的扫描范围
        self.MAX_SCAN_PAGES = 150  # 从 60 增加到 150

    async def extract_chapters(
        self,
        file_path: str,
        document_id: int,
        user_id: int,
        db: AsyncSession,
        ocr_result: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        智能提取章节（多策略）

        策略优先级：
        1. PDF 书签（最准确）
        2. 智能定位目录页（OCR）
        3. 扩大范围重试
        4. Fallback：全文档提取
        """

        print(f"\n{'='*70}")
        print(f"🧠 智能章节提取器启动")
        print(f"{'='*70}\n")

        # ========== 策略 1：PDF 书签 ==========
        print("📚 策略 1/4: 尝试提取 PDF 书签...")
        bookmark_result = await self._try_extract_bookmarks(file_path, document_id, user_id, db)
        if bookmark_result:
            return bookmark_result

        # ========== 策略 2：智能定位目录页 ==========
        print("\n🔍 策略 2/4: 智能定位目录页...")
        if ocr_result:
            located_result = await self._locate_toc_pages_smart(ocr_result, file_path, document_id, user_id, db)
            if located_result and self._validate_chapter_count(located_result):
                return located_result

        # ========== 策略 3：扩大范围重试 ==========
        print("\n🔄 策略 3/4: 扩大范围重试...")
        extended_result = await self._extended_range_extraction(file_path, document_id, user_id, db)
        if extended_result and self._validate_chapter_count(extended_result):
            return extended_result

        # ========== 策略 4：Fallback ==========
        print("\n⚠️  策略 4/4: 使用启发式 Fallback...")
        return await self._heuristic_fallback(file_path, document_id, user_id, db)

    async def _try_extract_bookmarks(
        self,
        file_path: str,
        document_id: int,
        user_id: int,
        db: AsyncSession
    ) -> Optional[List[Dict[str, Any]]]:
        """策略 1：提取 PDF 书签"""
        try:
            import fitz
            doc = fitz.open(file_path)
            toc = doc.get_toc()
            doc.close()

            if not toc or len(toc) < 3:
                print(f"   ❌ 书签太少或不存在（{len(toc) if toc else 0} 个）")
                return None

            print(f"   ✅ 找到 {len(toc)} 个书签")

            # 使用 LLM 清洗和结构化书签
            toc_text = self._format_bookmarks(toc)

            chapters = await self._llm_extract_from_toc(toc_text, document_id, user_id, db)

            if chapters and len(chapters) >= 3:
                print(f"   ✅ 从书签提取了 {len(chapters)} 个章节")
                return chapters
            else:
                print(f"   ⚠️  书签提取的章节数太少（{len(chapters)}）")
                return None

        except Exception as e:
            print(f"   ❌ 书签提取失败: {e}")
            return None

    async def _locate_toc_pages_smart(
        self,
        ocr_result: Dict[str, Any],
        file_path: str,
        document_id: int,
        user_id: int,
        db: AsyncSession
    ) -> Optional[List[Dict[str, Any]]]:
        """策略 2：智能定位目录页"""

        pages = ocr_result.get('pages', [])

        if not pages:
            print(f"   ❌ 没有 OCR 页面")
            return None

        print(f"   📄 分析 {len(pages)} 个 OCR 页面...")

        # 步骤 1：找到"目录"标题页
        toc_start_page = self._find_toc_start_page(pages)

        if toc_start_page is None:
            print(f"   ⚠️  未找到明确的目录起始页")
            return None

        print(f"   ✅ 目录起始页：第 {toc_start_page} 页")

        # 步骤 2：从起始页开始，取连续的目录页（通常 3-10 页）
        toc_pages = self._extract_continuous_toc_pages(pages, toc_start_page)

        print(f"   📖 提取了 {len(toc_pages)} 个连续目录页")

        # 步骤 3：合并文本
        toc_text = "\n\n".join([
            f"--- 第{p['page']}页 ---\n{p['text']}"
            for p in toc_pages
        ])

        print(f"   📝 目录文本长度：{len(toc_text)} 字符")

        # 步骤 4：LLM 提取
        chapters = await self._llm_extract_from_toc(toc_text, document_id, user_id, db)

        return chapters

    def _find_toc_start_page(self, pages: List[Dict]) -> Optional[int]:
        """找到目录起始页"""

        # 目录标题模式
        toc_title_patterns = [
            r'^目录\s*$',  # "目录"
            r'^目\s*录\s*$',  # "目　录"（可能有全角空格）
            r'^目\s+录$',  # "目   录"
            r'^Contents\s*$',  # "Contents"
            r'^TABLE OF CONTENTS\s*$',  # "TABLE OF CONTENTS"
            r'^章节目录\s*$',  # "章节目录"
            r'^课\s*题\s*$',  # "课题"
        ]

        for page_data in pages:
            text = page_data.get('text', '')
            page_num = page_data.get('page_num')

            # 提取前 500 字符（通常目录标题在开头）
            header = text[:500].strip()

            for pattern in toc_title_patterns:
                if re.search(pattern, header, re.IGNORECASE | re.MULTILINE):
                    print(f"      → 第 {page_num} 页匹配目录标题: {pattern}")
                    return page_num

        return None

    def _extract_continuous_toc_pages(
        self,
        pages: List[Dict],
        start_page: int
    ) -> List[Dict]:
        """从起始页开始，提取连续的目录页"""

        # 找到起始页的索引
        start_index = None
        for i, page in enumerate(pages):
            if page['page_num'] == start_page:
                start_index = i
                break

        if start_index is None:
            return []

        # 从起始页开始，连续取页，直到目录明显结束
        toc_pages = []
        consecutive_non_toc = 0  # 连续非目录页计数

        for i in range(start_index, min(start_index + 20, len(pages))):
            page = pages[i]
            text = page['text']

            # 检查这页是否还像目录页
            if self._is_likely_toc_page(text):
                toc_pages.append(page)
                consecutive_non_toc = 0
            else:
                consecutive_non_toc += 1
                if consecutive_non_toc > 2:  # 连续 2 页不像目录，就停止
                    break

        return toc_pages

    def _is_likely_toc_page(self, text: str) -> bool:
        """判断这页是否像目录页"""

        # 快速检查：必须有章节关键词
        chapter_indicators = [
            r'第[一二三四五六七八九十\d]+章',
            r'Chapter\s+\d+',
            r'[一二三四五六七八九十]+、',
            r'\d+\.\d+',  # 1.1, 1.2
        ]

        has_chapter = any(re.search(p, text) for p in chapter_indicators)

        if not has_chapter:
            return False

        # 计算目录特征分数
        score = 0

        # 页码密度
        page_pattern = r'\d+\s*[页pP]|P\.\s*\d+'
        page_count = len(re.findall(page_pattern, text))
        if page_count >= 3:
            score += 2

        # 章节编号密度
        chapter_count = 0
        for pattern in chapter_indicators:
            chapter_count += len(re.findall(pattern, text))
        if chapter_count >= 3:
            score += 3

        # 小节编号
        subsection_count = len(re.findall(r'\d+\.\d+', text))
        if subsection_count >= 5:
            score += 1

        return score >= 3

    async def _extended_range_extraction(
        self,
        file_path: str,
        document_id: int,
        user_id: int,
        db: AsyncSession
    ) -> Optional[List[Dict[str, Any]]]:
        """策略 3：扩大范围重试"""

        try:
            import fitz
            from app.core.ocr_engine import get_ocr_engine

            doc = fitz.open(file_path)
            total_pages = len(doc)
            doc.close()

            # 扫描更多页面（前 150 页）
            scan_range = min(self.MAX_SCAN_PAGES, total_pages)

            print(f"   📖 扩大扫描范围：前 {scan_range} 页")

            # 执行 OCR
            ocr_engine = get_ocr_engine()
            pages_to_ocr = list(range(1, scan_range + 1))

            print(f"   🔬 正在 OCR {len(pages_to_ocr)} 页...")

            ocr_result = ocr_engine.process_pdf(
                pdf_path=file_path,
                pages=pages_to_ocr
            )

            if not ocr_result['success']:
                print(f"   ❌ OCR 失败")
                return None

            # 使用智能定位策略
            chapters = await self._locate_toc_pages_smart(
                ocr_result, file_path, document_id, user_id, db
            )

            return chapters

        except Exception as e:
            print(f"   ❌ 扩大范围提取失败: {e}")
            return None

    async def _heuristic_fallback(
        self,
        file_path: str,
        document_id: int,
        user_id: int,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """策略 4：启发式 Fallback"""

        print(f"   🔄 使用启发式方法...")

        # 简单的正则提取
        try:
            import fitz
            doc = fitz.open(file_path)

            # 提取前 30 页的文本
            all_text = ""
            for i in range(min(30, len(doc))):
                page = doc[i]
                text = page.get_text()
                if text.strip():
                    all_text += f"\n--- 第{i+1}页 ---\n{text}"

            doc.close()

            # 使用 LLM 提取
            chapters = await self._llm_extract_from_toc(all_text, document_id, user_id, db)

            if chapters:
                return chapters
            else:
                # 最后的 fallback：返回一个默认章节
                print(f"   ⚠️  无法提取目录，创建默认章节")
                return [{
                    'chapter_number': 1,
                    'chapter_title': '全文',
                    'page_number': 1,
                    'subsections': []
                }]

        except Exception as e:
            print(f"   ❌ Fallback 失败: {e}")
            return []

    def _format_bookmarks(self, toc: list) -> str:
        """格式化书签为文本"""

        toc_parts = []
        for level, title, page_num in toc:
            indent = "  " * (level - 1)
            toc_parts.append(f"{indent}{'•' * level} {title} (第{page_num}页)")

        return "\n".join(toc_parts)

    async def _llm_extract_from_toc(
        self,
        toc_text: str,
        document_id: int,
        user_id: int,
        db: AsyncSession
    ) -> Optional[List[Dict[str, Any]]]:
        """使用 LLM 从目录文本提取章节"""

        print(f"   🧠 调用 LLM 提取章节...")
        print(f"   📝 文本长度：{len(toc_text)} 字符")

        try:
            import httpx

            prompt = f"""你是一个专业的教材目录识别专家。请从下面的文本中提取教材的目录结构。

【关键要求】：
1. **必须提取所有章节**，不要遗漏任何章节
2. **必须提取所有小节**，包括子小节
3. 如果目录很长（超过10章），也要全部提取
4. 注意：有些教材可能有附录、参考文献等，这些不算在主要章节内

【文本内容】：
```
{toc_text[:8000]}
```

【返回格式】（严格按照 JSON 格式）：
{{
  "has_toc": true,
  "confidence": "high",
  "total_chapters": 章节总数,
  "chapters": [
    {{
      "chapter_number": 1,
      "chapter_title": "章节标题",
      "page_number": 页码,
      "subsections": [
        {{"subsection_number": "1.1", "subsection_title": "小节标题", "page_number": 页码}}
      ]
    }}
  ]
}}

【注意】：
- 如果目录超过 8000 字符被截断，请告诉我，我会提供更多文本
- 必须提取完整，不要因为章节多就停止
"""

            # 调用 LLM
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
                        "temperature": 0.1,  # 降低温度，提高准确性
                        "max_tokens": 8000
                    }
                )

            if response.status_code != 200:
                print(f"   ❌ LLM 调用失败：{response.status_code}")
                return None

            result = response.json()
            content = result['choices'][0]['message']['content']

            # 解析 JSON
            # 提取 JSON 部分（可能包含在 ```json 中）
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = content

            data = json.loads(json_str)

            if not data.get('has_toc'):
                print(f"   ⚠️  LLM 认为没有目录")
                return None

            chapters = data.get('chapters', [])

            print(f"   ✅ LLM 提取了 {len(chapters)} 个章节")

            # 创建章节记录
            for chapter_info in chapters:
                await self._create_chapter_progress(
                    db, document_id, user_id, chapter_info
                )

            return chapters

        except json.JSONDecodeError as e:
            print(f"   ❌ JSON 解析失败: {e}")
            print(f"   📄 LLM 响应：{content[:500]}")
            return None
        except Exception as e:
            print(f"   ❌ LLM 提取失败: {e}")
            return None

    def _validate_chapter_count(self, chapters: List[Dict[str, Any]]) -> bool:
        """验证章节数量是否合理"""

        if not chapters:
            return False

        count = len(chapters)

        # 合理范围：3-30 章
        if count < 3:
            print(f"   ⚠️  章节数量太少：{count} 章")
            return False

        if count > 30:
            print(f"   ⚠️  章节数量异常多：{count} 章（可能有重复）")
            # 不返回 False，让用户决定

        print(f"   ✅ 章节数量合理：{count} 章")
        return True

    async def _create_chapter_progress(
        self,
        db: AsyncSession,
        document_id: int,
        user_id: int,
        chapter_info: Dict[str, Any]
    ):
        """创建章节进度记录"""

        from app.models.document import Progress
        from sqlalchemy import select

        # 检查是否已存在
        existing = await db.execute(
            select(Progress).where(
                Progress.document_id == document_id,
                Progress.chapter_number == chapter_info['chapter_number']
            )
        )
        if existing.scalar_one_or_none():
            return

        # 创建新记录
        progress = Progress(
            document_id=document_id,
            user_id=user_id,
            chapter_number=chapter_info['chapter_number'],
            chapter_title=chapter_info['chapter_title'],
            completion_percentage=0.0,
            time_spent_minutes=0,
            is_locked=True  # 默认锁定
        )

        db.add(progress)
        await db.commit()
