"""
章节划分服务 - 基于目录识别
使用 LLM 识别教材目录，提取章节结构
"""
import json
import re
from typing import List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, Progress
from app.core.config import settings


class ChapterDivider:
    """章节划分器：基于目录识别章节结构"""

    def __init__(self):
        # 通义千问 API 配置
        self.api_key = settings.DASHSCOPE_API_KEY
        self.model = "qwen-plus"  # 使用更强的模型

    async def extract_table_of_contents(
        self,
        document_text: str,
        document_title: str
    ) -> Dict[str, Any]:
        """
        从文档中提取目录

        Args:
            document_text: 文档文本内容
            document_title: 文档标题

        Returns:
            目录结构，包含章节列表
        """
        print(f"📚 开始提取目录: {document_title}")
        
        # 策略1: 提取前 10 页内容（通常目录在前几页）
        # 假设每页约 500-1000 字符，前 10 页约 5000-10000 字符
        toc_section = document_text[:10000]
        
        # 策略2: 查找包含"目录"、"Contents"等关键词的部分
        toc_keywords = ['目录', '目　录', 'Contents', 'TABLE OF CONTENTS', '章节目录']
        toc_start = -1
        
        for keyword in toc_keywords:
            idx = document_text.upper().find(keyword.upper())
            if idx != -1:
                # 找到目录关键词，提取其后的 5000 字符
                toc_section = document_text[idx:idx+5000]
                toc_start = idx
                print(f"✅ 找到目录关键词 '{keyword}' 在位置 {idx}")
                break
        
        if toc_start == -1:
            print("⚠️  未找到明确的目录关键词，使用前 10000 字符")
        
        # 使用 LLM 识别目录结构
        prompt = f"""你是一个专业的教材目录分析助手。请从以下文本中提取教材的目录结构，包括章节和小节。

文档标题：{document_title}

文本内容（可能包含目录）：
{toc_section}

请仔细分析文本，找出目录部分，并提取章节和小节信息。

目录的特征：
1. 通常包含"目录"、"Contents"等标题
2. 有清晰的章节编号，如"第一章"、"Chapter 1"、"1."等
3. 小节编号如"1.1"、"1.2"或"一、二、"等
4. 章节标题后可能有页码
5. 格式整齐，有明显的层级结构

请严格按照以下 JSON 格式返回，只返回 JSON，不要其他内容：

{{
    "has_toc": true/false,
    "total_chapters": 章节总数（数字）,
    "chapters": [
        {{
            "chapter_number": 1,
            "chapter_title": "章节标题（不包含章节号和页码）",
            "subsections": [
                {{
                    "subsection_number": 1,
                    "subsection_title": "小节标题（不包含小节号和页码）"
                }},
                {{
                    "subsection_number": 2,
                    "subsection_title": "小节标题（不包含小节号和页码）"
                }}
            ]
        }},
        {{
            "chapter_number": 2,
            "chapter_title": "章节标题（不包含章节号和页码）",
            "subsections": []
        }}
    ]
}}

注意：
1. 如果找不到明确的目录，设置 has_toc 为 false
2. 章节标题要简洁，去掉章节号和页码
3. 提取章节和小节，小节是可选的（如果没有小节，subsections 为空数组）
4. 章节编号和小节编号必须是连续的数字
5. 小节标题也要去掉编号和页码
"""

        try:
            import dashscope
            dashscope.api_key = self.api_key

            response = dashscope.Generation.call(
                model=self.model,
                prompt=prompt,
                result_format='message'
            )

            if response.status_code == 200:
                content = response.output.text
                print(f"📝 LLM 返回内容: {content[:300]}...")
                
                # 尝试提取 JSON
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                        
                        if result.get('has_toc', False) and result.get('chapters'):
                            print(f"✅ 成功从目录提取 {len(result['chapters'])} 个章节")
                            for ch in result['chapters'][:5]:  # 只打印前5个
                                print(f"   {ch['chapter_number']}. {ch['chapter_title']}")
                            return result
                        else:
                            print("⚠️  LLM 未找到明确的目录，使用启发式方法")
                            return self._heuristic_division(document_text, document_title)
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON 解析失败: {str(e)}")
                        return self._heuristic_division(document_text, document_title)
                else:
                    print("❌ 无法从 LLM 响应中提取 JSON")
                    return self._heuristic_division(document_text, document_title)
            else:
                raise Exception(f"LLM API 错误: {response.message}")

        except Exception as e:
            print(f"⚠️  LLM 分析失败: {str(e)}")
            return self._heuristic_division(document_text, document_title)

    def _heuristic_division(
        self,
        document_text: str,
        document_title: str
    ) -> Dict[str, Any]:
        """
        启发式章节划分（备用方案）
        在前 20000 字符中查找章节标记
        """
        print("📚 使用启发式方法提取章节...")
        
        # 只在前 20000 字符中查找（通常包含目录和前几章）
        search_text = document_text[:20000]
        
        # 查找章节标题模式（按优先级排序）
        patterns = [
            (r'第([一二三四五六七八九十百]+)章[\s\u3000：:]*([^\n]{2,50}?)(?=\s*\d+\s*$|\s*$|\n)', 'chinese_chapter'),
            (r'第(\d+)章[\s\u3000：:]*([^\n]{2,50}?)(?=\s*\d+\s*$|\s*$|\n)', 'number_chapter'),
            (r'Chapter\s+(\d+)[\s：:]*([^\n]{2,50}?)(?=\s*\d+\s*$|\s*$|\n)', 'english_chapter'),
            (r'^(\d+)\.[\s\u3000]+([^\n]{5,50})(?=\s*\d+\s*$|\s*$|\n)', 'number_dot'),
            (r'^([一二三四五六七八九十]+)、[\s\u3000]*([^\n]{5,50})(?=\s*\d+\s*$|\s*$|\n)', 'chinese_number'),
        ]

        chapters = []
        lines = search_text.split('\n')
        
        # 尝试每种模式
        for pattern, pattern_type in patterns:
            temp_chapters = []
            for line in lines:
                line = line.strip()
                if not line or len(line) > 100:  # 跳过空行和过长的行
                    continue
                
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    chapter_num_str = match.group(1)
                    chapter_title = match.group(2).strip() if len(match.groups()) > 1 else ""
                    
                    # 转换中文数字
                    if pattern_type in ['chinese_chapter', 'chinese_number']:
                        chapter_num = self._chinese_to_number(chapter_num_str)
                    else:
                        try:
                            chapter_num = int(chapter_num_str)
                        except:
                            continue
                    
                    # 清理标题（去掉页码、多余空格等）
                    chapter_title = re.sub(r'\s*\d+\s*$', '', chapter_title)  # 去掉末尾页码
                    chapter_title = chapter_title.strip('：: \t.．')
                    chapter_title = re.sub(r'\s+', ' ', chapter_title)  # 合并多个空格
                    
                    if chapter_title and 2 <= len(chapter_title) <= 50:
                        temp_chapters.append({
                            'chapter_number': chapter_num,
                            'chapter_title': chapter_title
                        })
            
            # 如果找到了章节，使用这个模式
            if len(temp_chapters) >= 2:
                chapters = temp_chapters
                print(f"✅ 使用模式 '{pattern_type}' 找到 {len(chapters)} 个章节")
                break
        
        # 如果没有找到明确的章节，创建默认章节
        if not chapters:
            print("⚠️  未找到明确章节标记，创建默认章节结构")
            # 根据文档长度决定章节数
            doc_length = len(document_text)
            if doc_length < 5000:
                total_chapters = 1
            elif doc_length < 20000:
                total_chapters = 3
            elif doc_length < 50000:
                total_chapters = 5
            else:
                total_chapters = 8
            
            for i in range(total_chapters):
                chapters.append({
                    'chapter_number': i + 1,
                    'chapter_title': f'第{i + 1}章'
                })

        # 去重和排序
        seen = set()
        unique_chapters = []
        for ch in sorted(chapters, key=lambda x: x['chapter_number']):
            if ch['chapter_number'] not in seen:
                seen.add(ch['chapter_number'])
                unique_chapters.append(ch)

        print(f"📊 最终识别到 {len(unique_chapters)} 个章节")
        for ch in unique_chapters[:10]:  # 只打印前10个
            print(f"   {ch['chapter_number']}. {ch['chapter_title']}")

        return {
            'has_toc': len(unique_chapters) >= 2,
            'total_chapters': len(unique_chapters),
            'chapters': unique_chapters
        }
    
    def _chinese_to_number(self, chinese_num: str) -> int:
        """将中文数字转换为阿拉伯数字"""
        chinese_map = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
            '百': 100
        }
        
        if chinese_num in chinese_map:
            return chinese_map[chinese_num]
        
        # 处理"十一"、"二十"等
        result = 0
        temp = 0
        for char in chinese_num:
            if char in chinese_map:
                num = chinese_map[char]
                if num >= 10:
                    temp = temp * num if temp else num
                else:
                    temp = num
            else:
                result += temp
                temp = 0
        result += temp
        
        return result if result > 0 else 1

    async def divide_document_into_chapters(
        self,
        document_id: int,
        user_id: int,
        document_text: str = None,
        db: AsyncSession = None
    ) -> List[Dict[str, Any]]:
        """
        将文档划分为章节并创建进度记录

        Args:
            document_id: 文档 ID
            user_id: 用户 ID
            document_text: 文档文本（可选，如果不提供则从数据库获取）
            db: 数据库会话

        Returns:
            划分的章节列表
        """
        # 获取文档信息
        doc_result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = doc_result.scalar_one_or_none()

        if not document:
            raise ValueError("文档不存在")

        document_title = document.title or document.filename

        # 如果没有提供文本，尝试从 ChromaDB 获取
        if not document_text:
            try:
                from app.core.chroma import get_document_collection
                
                collection = get_document_collection(document.md5_hash)
                if collection and collection.count() > 0:
                    # 获取所有文档块
                    results = collection.get()
                    if results and results['documents']:
                        # 合并所有 chunks 重建文档文本
                        document_text = "\n\n".join(results['documents'])
                        print(f"✅ 从 ChromaDB 恢复了文档文本，共 {len(document_text)} 字符")
                    else:
                        raise ValueError("无法获取文档内容")
                else:
                    raise ValueError("文档集合不存在或为空")
            except Exception as e:
                print(f"⚠️  从 ChromaDB 获取文本失败: {str(e)}")
                raise ValueError("无法获取文档内容，请重新上传文档")

        # 提取目录结构
        print(f"📖 开始分析文档: {document_title}")
        print(f"📄 文档长度: {len(document_text)} 字符")

        toc_result = await self.extract_table_of_contents(
            document_text,
            document_title
        )

        chapters = toc_result.get('chapters', [])
        total_chapters = len(chapters)

        print(f"✅ 识别到 {total_chapters} 个章节")

        # 为每个章节创建 Progress 记录和 Subsection 记录
        created_chapters = []

        for chapter_info in chapters:
            chapter_number = chapter_info.get('chapter_number', len(created_chapters) + 1)
            chapter_title = chapter_info.get('chapter_title', f'第{chapter_number}章')
            subsections_data = chapter_info.get('subsections', [])

            # 检查是否已存在该章节
            existing = await db.execute(
                select(Progress).where(
                    Progress.user_id == user_id,
                    Progress.document_id == document_id,
                    Progress.chapter_number == chapter_number
                )
            )
            existing_progress = existing.scalar_one_or_none()

            if not existing_progress:
                # 创建新的章节进度记录
                from app.schemas.document import ProgressCreate

                new_progress = await create_progress(
                    db,
                    ProgressCreate(
                        user_id=user_id,
                        document_id=document_id,
                        chapter_number=chapter_number,
                        chapter_title=chapter_title,
                        cognitive_level_assigned=3  # 默认中等难度
                    )
                )

                created_chapters.append({
                    'id': new_progress.id,
                    'chapter_number': chapter_number,
                    'chapter_title': chapter_title,
                    'status': 'locked' if chapter_number > 1 else 'not_started',  # 第一章解锁
                    'is_locked': chapter_number > 1,
                    'subsections_count': len(subsections_data)
                })

                print(f"  ✨ 创建章节 {chapter_number}: {chapter_title}")
            else:
                created_chapters.append({
                    'id': existing_progress.id,
                    'chapter_number': existing_progress.chapter_number,
                    'chapter_title': existing_progress.chapter_title,
                    'status': existing_progress.status,
                    'is_locked': False,
                    'subsections_count': len(subsections_data)
                })

            # 创建小节记录
            if subsections_data:
                from app.models.subsection import Subsection
                
                for subsection_info in subsections_data:
                    subsection_number = subsection_info.get('subsection_number')
                    subsection_title = subsection_info.get('subsection_title', f'{chapter_number}.{subsection_number}')
                    
                    # 检查小节是否已存在
                    existing_subsection = await db.execute(
                        select(Subsection).where(
                            Subsection.document_id == document_id,
                            Subsection.chapter_number == chapter_number,
                            Subsection.subsection_number == subsection_number
                        )
                    )
                    
                    if not existing_subsection.scalar_one_or_none():
                        new_subsection = Subsection(
                            document_id=document_id,
                            chapter_number=chapter_number,
                            subsection_number=subsection_number,
                            subsection_title=subsection_title,
                            estimated_time_minutes=15
                        )
                        db.add(new_subsection)
                        print(f"    📝 创建小节 {chapter_number}.{subsection_number}: {subsection_title}")
                
                await db.commit()

        # 更新文档的总章节数
        from app.crud.document import update_document_status
        await update_document_status(
            db,
            document_id,
            status="completed",
            total_pages=document.total_pages or 0,
            total_chapters=total_chapters,
            title=document_title
        )

        return created_chapters


# 辅助函数：创建进度记录
async def create_progress(
    db: AsyncSession,
    progress_data
):
    """创建进度记录"""
    from app.models.document import Progress

    new_progress = Progress(**progress_data.model_dump())
    db.add(new_progress)
    await db.commit()
    await db.refresh(new_progress)

    return new_progress
