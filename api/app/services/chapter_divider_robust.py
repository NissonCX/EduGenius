"""
章节划分服务 - 基于正则表达式的鲁棒提取

不依赖LLM，直接从目录文本中提取所有章节和小节
"""
import re
import json
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.document import Document, Progress
from app.core.config import settings


class RobustChapterDivider:
    """鲁棒的章节划分器 - 使用正则表达式"""

    def __init__(self):
        pass

    async def divide_document_into_chapters(
        self,
        document_id: int,
        user_id: int,
        document_text: str,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        使用正则表达式直接提取章节和小节

        优点：
        1. 不依赖LLM API
        2. 速度快
        3. 结果可预测
        4. 能识别所有章节（不只是前几章）
        """
        print(f"\n{'='*60}")
        print(f"📚 开始处理文档 {document_id} 的章节划分")
        print(f"{'='*60}\n")

        print(f"📄 目录文本长度: {len(document_text)} 字符")

        # 提取所有章节
        chapters = self._extract_chapters_with_regex(document_text)

        if chapters:
            print(f"\n✅ 成功提取 {len(chapters)} 个章节:\n")
            for ch in chapters:
                subs = ch.get('subsections', [])
                print(f"   第{ch['chapter_number']}章: {ch['chapter_title']}")
                if subs:
                    print(f"      小节数: {len(subs)}")
                    for sub in subs[:3]:
                        print(f"        - {sub['subsection_number']} {sub['subsection_title']}")
                    if len(subs) > 3:
                        print(f"        ... 共 {len(subs)} 个小节")

            # 创建进度记录
            for chapter_info in chapters:
                await self._create_chapter_and_subsections(
                    db, document_id, user_id, chapter_info
                )

            return chapters
        else:
            print("\n⚠️ 未能识别章节，创建默认章节\n")
            return await self._create_default_chapter(db, document_id, user_id)

    def _extract_chapters_with_regex(self, text: str) -> List[Dict[str, Any]]:
        """
        使用多层正则表达式提取章节和小节

        策略：
        1. 识别所有章节标题
        2. 对每个章节，识别其下属的小节
        """
        chapters = []

        # 章节标题模式（多种格式）
        chapter_patterns = [
            # 第一章 xxxxx
            (r'第([一二三四五六七八九十百千]+)\s*章[：:\s]*([^\n]{2,100}?)(?=\n第|\n\s*第|\n\s*\d+\.|\n\n|$)', 'chinese'),
            # 第1章 xxxxx
            (r'第(\d+)\s*章[：:\s]*([^\n]{2,100}?)(?=\n第|\n\s*第|\n\s*\d+\.|\n\n|$)', 'number'),
            # Chapter 1 xxxxx
            (r'Chapter\s+(\d+)[：:\s]*([^\n]{5,100}?)(?=\n\s*Chapter|\n\n|$)', 'english'),
            # 1. xxxxx
            (r'^(\d+)\.\s+([^\n]{5,100}?)(?=\n\s*\d+\.\s|\n\n|$)', 'dot'),
        ]

        # 第一步：提取所有章节
        for pattern, ptype in chapter_patterns:
            matches = list(re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE))

            if not matches:
                continue

            print(f"🔍 使用 '{ptype}' 模式找到 {len(matches)} 个章节候选")

            for match in matches:
                try:
                    chapter_num_str = match.group(1)
                    chapter_title = match.group(2).strip()

                    # 清理标题
                    chapter_title = re.sub(r'\s+', ' ', chapter_title)  # 规范空格
                    chapter_title = re.sub(r'\s*\d+\s*$', '', chapter_title)  # 移除页码

                    # 转换章节号
                    if ptype == 'chinese':
                        chapter_num = self._chinese_to_number(chapter_num_str)
                    else:
                        chapter_num = int(chapter_num_str)

                    # 过滤重复和无效标题
                    if len(chapter_title) < 2:
                        continue

                    # 检查是否已存在
                    if any(c['chapter_number'] == chapter_num for c in chapters):
                        continue

                    chapter = {
                        'chapter_number': chapter_num,
                        'chapter_title': chapter_title,
                        'page_number': 1,
                        'subsections': []
                    }

                    chapters.append(chapter)

                except (ValueError, AttributeError, IndexError) as e:
                    print(f"   ⚠️  解析章节失败: {e}")
                    continue

            if chapters:
                break  # 找到章节后停止尝试其他模式

        # 第二步：为每个章节提取小节
        if chapters:
            print(f"\n🔍 开始提取小节...")
            for chapter in chapters:
                subsections = self._extract_subsections_for_chapter(
                    text,
                    chapter['chapter_number'],
                    chapter['chapter_title']
                )
                chapter['subsections'] = subsections

        return chapters

    def _extract_subsections_for_chapter(
        self,
        text: str,
        chapter_number: int,
        chapter_title: str
    ) -> List[Dict[str, Any]]:
        """
        为指定章节提取小节

        策略：
        1. 找到章节标题的位置
        2. 从该位置开始，到下一个章节标题之间，查找小节
        """
        subsections = []

        # 查找章节位置
        chapter_pattern = rf'第{self._number_to_chinese(chapter_number)}\s*章.*?{chapter_title[:10]}'
        chapter_match = re.search(chapter_pattern, text)

        if not chapter_match:
            # 尝试其他格式
            chapter_pattern = rf'第{chapter_number}\s*章.*?{chapter_title[:10]}'
            chapter_match = re.search(chapter_pattern, text)

        if not chapter_match:
            return subsections

        chapter_start = chapter_match.start()

        # 查找下一个章节的位置
        next_chapter_patterns = [
            rf'第{self._number_to_chinese(chapter_number + 1)}\s*章',
            rf'第{chapter_number + 1}\s*章',
            rf'Chapter\s*{chapter_number + 1}',
            rf'^{chapter_number + 1}\.'
        ]

        chapter_end = len(text)
        for pattern in next_chapter_patterns:
            match = re.search(pattern, text[chapter_start:])
            if match:
                chapter_end = chapter_start + match.start()
                break

        # 在章节范围内提取小节
        chapter_text = text[chapter_start:chapter_end]

        # 小节模式
        subsection_patterns = [
            # 1.1 xxxxx 或 1.1. xxxxx
            (rf'{chapter_number}\.(\d+\.?\d*)\s*[.、:：]?\s*([^\n]{{2,80}}?)(?=\n{chapter_number}\.|\n\s*第|\n\n|$)', 'dot'),
            # 第一节 xxxxx
            (rf'第([一二三四五六七八九十]+)\s*节\s*[.、:：]?\s*([^\n]{{2,80}}?)(?=\n第|\n\n|$)', 'chinese'),
            # （1）xxxxx
            (rf'（([一二三四五六七八九十]+)）\s*([^\n]{{2,80}}?)(?=\n（|\n\n|$)', 'parenthesis'),
        ]

        for pattern, ptype in subsection_patterns:
            matches = re.finditer(pattern, chapter_text, re.MULTILINE)
            sub_count = 0

            for match in matches:
                try:
                    if ptype == 'dot':
                        sub_num_str = match.group(1)
                        sub_title = match.group(2).strip()
                        sub_num = f"{chapter_number}.{sub_num_str}"
                    elif ptype == 'chinese':
                        sub_num_chinese = match.group(1)
                        sub_num = f"{chapter_number}.{self._chinese_to_number(sub_num_chinese)}"
                        sub_title = match.group(2).strip()
                    elif ptype == 'parenthesis':
                        sub_num_chinese = match.group(1)
                        sub_num = f"{chapter_number}.{self._chinese_to_number(sub_num_chinese)}"
                        sub_title = match.group(2).strip()
                    else:
                        continue

                    # 清理标题
                    sub_title = re.sub(r'\s+', ' ', sub_title)
                    sub_title = re.sub(r'\s*\d+\s*$', '', sub_title)

                    if len(sub_title) < 2:
                        continue

                    subsections.append({
                        'subsection_number': sub_num,
                        'subsection_title': sub_title,
                        'page_number': 1
                    })
                    sub_count += 1

                except (ValueError, AttributeError, IndexError):
                    continue

            if subsections:
                print(f"   第{chapter_number}章: 提取到 {len(subsections)} 个小节 (使用{ptype}模式)")
                break

        return subsections

    def _number_to_chinese(self, num: int) -> str:
        """数字转中文"""
        chinese_map = {
            1: '一', 2: '二', 3: '三', 4: '四', 5: '五',
            6: '六', 7: '七', 8: '八', 9: '九', 10: '十'
        }
        return chinese_map.get(num, str(num))

    def _chinese_to_number(self, chinese_num: str) -> int:
        """中文转数字"""
        chinese_map = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
            '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15,
            '十六': 16, '十七': 17, '十八': 18, '十九': 19, '二十': 20
        }
        return chinese_map.get(chinese_num, 1)

    async def _create_chapter_and_subsections(
        self,
        db: AsyncSession,
        document_id: int,
        user_id: int,
        chapter_info: Dict[str, Any]
    ):
        """创建章节和小节记录"""
        try:
            # 获取用户认知等级
            user_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            cognitive_level = user.cognitive_level if user else 3

            # 创建章节进度
            progress = Progress(
                user_id=user_id,
                document_id=document_id,
                chapter_number=chapter_info['chapter_number'],
                chapter_title=chapter_info['chapter_title'],
                cognitive_level_assigned=cognitive_level,
                completion_percentage=0,
                time_spent_minutes=0
            )

            db.add(progress)
            await db.commit()

            # 创建小节
            if 'subsections' in chapter_info and chapter_info['subsections']:
                from sqlalchemy import text
                for subsection_info in chapter_info['subsections']:
                    try:
                        insert_stmt = text("""
                            INSERT INTO subsections
                            (user_id, document_id, chapter_number, subsection_number,
                             subsection_title, page_number, cognitive_level_assigned,
                             completion_percentage, time_spent_minutes)
                            VALUES (:user_id, :document_id, :chapter_number, :subsection_number,
                                    :subsection_title, :page_number, :cognitive_level,
                                    :completion_pct, :time_spent)
                        """)

                        await db.execute(insert_stmt, {
                            'user_id': user_id,
                            'document_id': document_id,
                            'chapter_number': chapter_info['chapter_number'],
                            'subsection_number': subsection_info.get('subsection_number', ''),
                            'subsection_title': subsection_info.get('subsection_title', ''),
                            'page_number': subsection_info.get('page_number', 1),
                            'cognitive_level': cognitive_level,
                            'completion_pct': 0.0,
                            'time_spent': 0.0
                        })
                    except Exception as e:
                        print(f"      ⚠️  创建小节失败: {e}")

                await db.commit()

        except Exception as e:
            print(f"❌ 创建章节进度失败: {e}")

    async def _create_default_chapter(
        self,
        db: AsyncSession,
        document_id: int,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """创建默认章节"""
        doc_result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = doc_result.scalar_one_or_none()
        doc_title = document.title if document else "完整教材"

        default_chapter = {
            'chapter_number': 1,
            'chapter_title': doc_title,
            'page_number': 1,
            'subsections': []
        }

        await self._create_chapter_and_subsections(
            db, document_id, user_id, default_chapter
        )

        return [default_chapter]
