"""
智能PDF教科书解析器 - 先搜寻、再定位、后提取

实现策略：
1. 书签优先：使用PyMuPDF的get_toc()提取书签
2. 启发式扫描：扫描前60页，计算关键词权重
3. 智能定位：选出权重最高的连续2-5页
4. 异步处理：避免阻塞
"""
import fitz  # PyMuPDF
import re
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession


class TextbookParser:
    """智能教科书解析器"""

    # 目录关键词及其权重
    TOC_KEYWORDS = {
        '目录': 10,
        '目　录': 10,
        'Contents': 10,
        'TABLE OF CONTENTS': 10,
        '章节目录': 8,
        'CONTENTS': 8,
        '课　题': 5,
    }

    # 章节关键词
    CHAPTER_KEYWORDS = {
        '章': 3,
        'Chapter': 3,
        '节': 2,
        'Section': 2,
    }

    # 页码模式
    PAGE_PATTERNS = [
        r'\d+\s*[页p]',  # "15页" or "15p"
        r'P\.\s*\d+',     # "P.15"
        r'－\d+\s*－',    # "－15－"
    ]

    def __init__(self):
        self.max_scan_pages = 60  # 扫描前60页

    async def parse_textbook(
        self,
        file_path: str,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        解析教科书PDF

        Returns:
            {
                'toc_text': str,  # 提取的目录文本
                'source': 'bookmark' | 'scan',  # 来源
                'pages': List[int],  # 目录页码列表
                'need_ai_guess': bool  # 是否需要AI猜测
            }
        """
        print(f"\n{'='*60}")
        print(f"📚 开始智能解析教科书: {file_path}")
        print(f"{'='*60}\n")

        # 第一步：尝试提取书签
        print("🔍 第一步：尝试提取PDF书签...")
        bookmark_result = self._extract_bookmarks(file_path)

        if bookmark_result['success'] and bookmark_result['has_content']:
            print(f"✅ 书签提取成功！找到 {len(book_result['toc'])} 个条目\n")
            return {
                'toc_text': bookmark_result['toc_text'],
                'source': 'bookmark',
                'pages': bookmark_result['pages'],
                'need_ai_guess': False
            }

        # 第二步：启发式扫描
        print("⚠️  书签提取失败或内容不足，开始启发式扫描...\n")
        scan_result = await self._heuristic_scan(file_path)

        return {
            'toc_text': scan_result['toc_text'],
            'source': 'scan',
            'pages': scan_result['pages'],
            'need_ai_guess': scan_result.get('need_ai_guess', False)
        }

    def _extract_bookmarks(self, file_path: str) -> Dict[str, Any]:
        """
        提取PDF书签（TOC）

        PyMuPDF的get_toc()可以直接提取PDF的目录结构
        """
        try:
            doc = fitz.open(file_path)
            toc = doc.get_toc()

            # 🔧 FIX: 放宽书签要求，只要有任何书签就使用
            if not toc or len(toc) < 1:
                return {
                    'success': False,
                    'has_content': False,
                    'toc': [],
                    'pages': [],
                    'toc_text': ''
                }

            print(f"   📖 找到 {len(toc)} 个书签条目")

            # 分析书签层级
            max_level = max([item[1] for item in toc]) if toc else 0

            # 🔧 FIX: 移除层级限制，即使只有1层（只有章节）也可以
            # if max_level < 2:
            #     print(f"   ⚠️  书签层级太浅（{max_level}），不足以构建完整目录")
            #     return {
            #         'success': False,
            #         'has_content': False,
            #         'toc': [],
            #         'pages': [],
            #         'toc_text': ''
            #     }

            # 构建目录树
            toc_text_parts = []
            pages_set = set()

            for item in toc:
                level, title, page_num = item[1], item[0], item[2]

                # 格式化为层级文本
                indent = "  " * (level - 1)
                toc_text_parts.append(f"{indent}{'•' * level} {title} (第{page_num}页)")
                pages_set.add(page_num)

            toc_text = "\n".join(toc_text_parts)

            print(f"   ✅ 书签目录构建成功：")
            print(f"      - 层级深度: {max_level}")
            print(f"      - 页面范围: {min(pages_set)}-{max(pages_set)}")
            print(f"      - 文本长度: {len(toc_text)} 字符")

            return {
                'success': True,
                'has_content': True,
                'toc': toc,
                'pages': sorted(list(pages_set)),
                'toc_text': toc_text
            }

        except Exception as e:
            print(f"   ❌ 书签提取失败: {e}")
            return {
                'success': False,
                'has_content': False,
                'toc': [],
                'pages': [],
                'toc_text': ''
            }

    async def _heuristic_scan(self, file_path: str) -> Dict[str, Any]:
        """
        启发式扫描：扫描前N页，计算关键词权重

        Returns:
            {
                'toc_text': str,
                'pages': List[int],
                'need_ai_guess': bool
            }
        """
        print(f"🔍 第二步：启发式扫描前 {self.max_scan_pages} 页...\n")

        try:
            doc = fitz.open(file_path)
            page_scores = []

            # 扫描每一页并计算权重
            for page_num in range(min(self.max_scan_pages, len(doc))):
                page = doc[page_num]
                text = page.get_text()

                if not text.strip():
                    continue

                # 计算关键词权重
                score = self._calculate_page_score(text, page_num)

                if score > 0:
                    page_scores.append({
                        'page': page_num + 1,
                        'score': score,
                        'text': text,
                        'char_count': len(text)
                    })

                    # 显示前几页的分数
                    if page_num < 10:
                        status = "✅" if score > 20 else "  "
                        print(f"   {status} 第 {page_num + 1:2} 页: {score:3} 分 | {len(text):4} 字符")

            doc.close()

            if not page_scores:
                print("   ⚠️  未找到任何有价值的页面")
                # 返回前10页作为fallback
                doc = fitz.open(file_path)
                fallback_texts = []
                for i in range(min(10, len(doc))):
                    text = doc[i].get_text().strip()
                    if text:
                        fallback_texts.append(text)
                doc.close()

                return {
                    'toc_text': "\n\n".join(f"--- 第{i+1}页 ---\n{text}" for i, text in enumerate(fallback_texts)),
                    'pages': list(range(1, len(fallback_texts) + 1)),
                    'need_ai_guess': True
                }

            # 按分数排序
            page_scores.sort(key=lambda x: x['score'], reverse=True)

            print(f"\n   📊 页面权重排名:")
            for item in page_scores[:10]:
                print(f"      第{item['page']:2}页: {item['score']:3} 分")

            # 智能定位：选出权重最高的连续2-5页
            best_pages = self._select_best_pages(page_scores)

            print(f"\n   ✅ 选定的目录页: {[p['page'] for p in best_pages]}")

            # 合并文本
            toc_text = "\n\n".join([
                f"--- 第{p['page']}页 ---\n{p['text']}"
                for p in best_pages
            ])

            print(f"   📄 提取文本长度: {len(toc_text)} 字符\n")

            return {
                'toc_text': toc_text,
                'pages': [p['page'] for p in best_pages],
                'need_ai_guess': False
            }

        except Exception as e:
            print(f"❌ 启发式扫描失败: {e}")
            import traceback
            traceback.print_exc()

            # Fallback: 返回前10页
            doc = fitz.open(file_path)
            fallback_texts = []
            for i in range(min(10, len(doc))):
                text = doc[i].get_text().strip()
                if text:
                    fallback_texts.append(text)
            doc.close()

            return {
                'toc_text': "\n\n".join(f"--- 第{i+1}页 ---\n{text}" for i, text in enumerate(fallback_texts)),
                'pages': list(range(1, len(fallback_texts) + 1)),
                'need_ai_guess': True
            }

    def _calculate_page_score(self, text: str, page_num: int) -> int:
        """计算页面的目录可能性权重"""
        score = 0

        # 1. 检查目录关键词（高权重）
        for keyword, weight in self.TOC_KEYWORDS.items():
            if keyword in text:
                score += weight
                # 如果标题独立出现，额外加分
                if text.strip().startswith(keyword):
                    score += 5

        # 2. 检查章节关键词（中权重）
        for keyword, weight in self.CHAPTER_KEYWORDS.items():
            # 统计关键词出现次数
            count = text.count(keyword)
            if count > 0:
                # 前几页的章节更可能是目录
                position_bonus = max(0, 5 - page_num)  # 前5页有额外加分
                score += min(count * weight * position_bonus, 50)

        # 3. 检查页码模式（中权重）
        page_count = 0
        for pattern in self.PAGE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            page_count += len(matches)

        if page_count > 0:
            # 页码密度：页码数量 / 文本长度
            density = page_count / len(text) * 1000
            score += min(int(density), 10)

        # 4. 检查章节编号模式（高权重）
        chapter_patterns = [
            r'第[一二三四五六七八九十百千]+章',
            r'第\d+章',
            r'Chapter\s+\d+',
            r'[一二三四五六七八九十]+、[^\n]{1,20}',
        ]
        for pattern in chapter_patterns:
            matches = re.findall(pattern, text)
            if matches:
                score += len(matches) * 3

        # 5. 检查小节编号
        section_patterns = [
            r'\d+\.\d+',  # 1.1, 1.2
            r'第[一二三四五六七八九十]+节',
        ]
        for pattern in section_patterns:
            matches = re.findall(pattern, text)
            if matches:
                score += len(matches) * 2

        return score

    def _select_best_pages(
        self,
        page_scores: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        智能定位：选出权重最高的连续页面（不限制页数）

        策略：
        1. 排序后取所有高分页面（分数 >= 5）
        2. 找出权重最高的页面作为中心
        3. 向前后扩展，包含连续的页面（只要有合理分数）
        4. 不限制页数上限（最多20页），确保完整TOC被提取
        """
        if not page_scores:
            return []

        # 排序
        sorted_pages = sorted(page_scores, key=lambda x: x['score'], reverse=True)

        # 🔧 FIX: 取所有有意义的页面（分数 >= 5），而不是只取前10个
        min_score_threshold = 5  # 最低分数阈值
        scoring_pages = [p for p in sorted_pages if p['score'] >= min_score_threshold]

        if not scoring_pages:
            # 如果没有高分页面，fallback到前2页
            print(f"   ⚠️  没有找到高分页面（>={min_score_threshold}分），使用前2页")
            return sorted_pages[:2]

        print(f"   📊 找到 {len(scoring_pages)} 个高分页面（>={min_score_threshold}分）")

        # 找出最高分的页面作为起始点
        start_index = 0
        max_score = scoring_pages[0]['score']

        for i, page in enumerate(scoring_pages):
            if page['score'] == max_score:
                start_index = i
                break

        # 从起始点向前后扩展
        selected_pages = [scoring_pages[start_index]]
        selected_page_nums = {scoring_pages[start_index]['page']}

        # 向前扩展
        for i in range(start_index - 1, -1, -1):
            if i < 0:
                break
            prev_page = scoring_pages[i]['page']
            # 只包含连续页码
            if prev_page == selected_page_nums[min(selected_pages)] - 1:
                selected_pages.insert(0, scoring_pages[i])
                selected_page_nums.add(prev_page)
            else:
                break

            # 🔧 FIX: 移除5页限制，扩展到20页
            if len(selected_pages) >= 20:
                print(f"   ⏹️  扩展达到20页，停止")
                break

        # 向后扩展
        for i in range(start_index + 1, len(scoring_pages)):
            next_page = scoring_pages[i]['page']
            # 只包含连续页码
            if next_page == max(selected_page_nums) + 1:
                selected_pages.append(scoring_pages[i])
                selected_page_nums.add(next_page)
            else:
                break

            # 🔧 FIX: 移除5页限制，扩展到20页
            if len(selected_pages) >= 20:
                print(f"   ⏹️  扩展达到20页，停止")
                break

        # 至少返回2页
        if len(selected_pages) < 2:
            print(f"   ⚠️  选中的页面太少({len(selected_pages)})，补充到2页")
            # 补充最高分的页面
            for page in sorted_pages:
                if page['page'] not in selected_page_nums:
                    selected_pages.append(page)
                    selected_page_nums.add(page['page'])
                    if len(selected_pages) >= 2:
                        break

        # 按页码排序
        selected_pages.sort(key=lambda x: x['page'])

        print(f"   ✅ 最终选中 {len(selected_pages)} 页: {[p['page'] for p in selected_pages]}")

        return selected_pages
