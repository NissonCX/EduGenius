"""
增强版文档处理服务 - 正确处理教科书目录

业务流程：
1. 单独提取前几页（可能是目录页）
2. 识别真正的目录页
3. 从目录页提取纯文本用于章节分析
4. 正文内容单独处理（不包含目录）
"""
import os
import hashlib
import fitz  # PyMuPDF
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
import dashscope
from dashscope import TextEmbedding

from app.core.config import settings


class EnhancedDocumentProcessor:
    """增强版文档处理器：正确处理目录和正文"""

    def __init__(self):
        # 配置文本切分器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
        )

        # 配置 DashScope Embedding
        dashscope.api_key = settings.DASHSCOPE_API_KEY

    def calculate_md5(self, file_path: str) -> str:
        """计算文件的 MD5 哈希"""
        md5_hash = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()

    def extract_toc_pages(
        self,
        file_path: str,
        max_toc_pages: int = 15  # 增加到15页，确保包含完整目录
    ) -> Tuple[List[str], str]:
        """
        提取前几页（可能是目录页）
        返回：(目录页列表, 合并的目录文本)
        """
        print(f"📖 正在提取前 {max_toc_pages} 页...")

        try:
            with fitz.open(file_path) as doc:
                toc_pages = []
                toc_text_parts = []
                found_toc_keyword = False
                consecutive_non_toc_pages = 0
                max_consecutive_non_toc = 3  # 允许连续3页非目录后停止

                # 只提取前几页
                for page_num in range(min(max_toc_pages, len(doc))):
                    page = doc[page_num]
                    text = page.get_text().strip()

                    if text:
                        toc_pages.append(text)
                        # 检查是否包含目录特征
                        toc_keywords = ['目录', '目　录', 'Contents', 'TABLE OF CONTENTS',
                                        '章节目录', 'CONTENTS', '课　题']
                        has_toc_keyword = any(keyword in text for keyword in toc_keywords)

                        # 检查是否包含章节标记（如"第一章"、"第1章"）
                        import re
                        has_chapter_marker = re.search(r'第[一二三四五六七八九十\d]+\s*章', text)

                        # 判断是否应该包含这一页
                        should_include = False

                        if has_toc_keyword:
                            print(f"   ✅ 第 {page_num + 1} 页发现目录关键词")
                            should_include = True
                            found_toc_keyword = True
                            consecutive_non_toc_pages = 0  # 重置计数器
                        elif has_chapter_marker:
                            # 如果发现章节标记
                            if found_toc_keyword or consecutive_non_toc_pages < max_consecutive_non_toc:
                                print(f"   🔍 第 {page_num + 1} 页发现章节标记")
                                should_include = True
                                consecutive_non_toc_pages = 0
                            else:
                                consecutive_non_toc_pages += 1
                        else:
                            # 普通页面
                            if found_toc_keyword and consecutive_non_toc_pages < max_consecutive_non_toc:
                                # 在目录区域后，允许一些非目录页（如空白页、过渡页）
                                print(f"   📄 第 {page_num + 1} 页: {len(text)} 字符（目录区域）")
                                should_include = True
                                consecutive_non_toc_pages += 1
                            else:
                                print(f"   📄 第 {page_num + 1} 页: {len(text)} 字符")
                                consecutive_non_toc_pages += 1

                        # 如果应该包含，添加到目录文本
                        if should_include:
                            toc_text_parts.append(text)

                        # 如果连续太多页都不是目录，停止提取
                        if consecutive_non_toc_pages >= max_consecutive_non_toc and found_toc_keyword:
                            print(f"   ⏹️  已连续{max_consecutive_non_toc}页非目录，停止提取")
                            break

                # 如果没有找到明确的目录关键词，返回前5页内容让LLM判断
                if not toc_text_parts and toc_pages:
                    print(f"   ⚠️  未发现明确的目录，返回前 {min(5, len(toc_pages))} 页供分析")
                    toc_text_parts = toc_pages[:min(5, len(toc_pages))]
                elif len(toc_text_parts) < 3 and toc_pages:
                    # 如果找到的目录内容太少，补充更多页面
                    additional_pages = min(8, len(toc_pages))  # 增加到8页
                    print(f"   📎 目录内容较少，补充到前 {additional_pages} 页")
                    toc_text_parts = toc_pages[:additional_pages]

                # 合并目录页文本
                combined_toc = "\n\n".join(toc_text_parts)
                print(f"📚 目录提取完成: {len(combined_toc)} 字符，共 {len(toc_text_parts)} 页\n")

                return toc_pages, combined_toc

        except Exception as e:
            print(f"❌ PDF 读取失败: {str(e)}")
            raise

    def identify_chapter_patterns(
        self,
        toc_text: str
    ) -> Dict[str, Any]:
        """
        从目录文本中识别章节模式
        """
        print("🔍 正在识别章节模式...")

        import re

        # 检查不同的目录格式
        patterns_found = {}

        # 中文教材常见格式
        if re.search(r'第[一二三四五六七八九十百]+章', toc_text):
            patterns_found['format'] = '中文章节（一二三）'
        elif re.search(r'第\d+章', toc_text):
            patterns_found['format'] = '中文章节（数字）'
        elif re.search(r'Chapter\s*\d+', toc_text, re.IGNORECASE):
            patterns_found['format'] = '英文章节（Chapter）'
        elif re.search(r'^\d+\.', toc_text, re.MULTILINE):
            patterns_found['format'] = '数字点（1. 2.）'

        # 统计可能的章节数
        chapter_count = len(re.findall(
            r'(?:第[一二三四五六七八九十百]+章|第\d+章|Chapter\s*\d+|^\d+\.)',
            toc_text,
            re.MULTILINE
        ))

        patterns_found['estimated_chapters'] = chapter_count

        print(f"   检测到格式: {patterns_found.get('format', '未知')}")
        print(f"   估计章节数: {chapter_count}")

        return patterns_found

    async def process_pdf_v2(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        处理 PDF 文件（增强版）

        返回包含：
        - toc_text: 纯净的目录文本
        - content_texts: 正文内容（按页）
        - chunks: 切分后的文档块
        - embeddings: 向量
        - texts: 所有文本
        - stats: 统计信息
        """
        print("=" * 60)
        print(f"📄 开始处理文档: {metadata.get('title', 'Unknown')}")
        print("=" * 60)

        # 步骤1: 提取目录页
        # 🔧 FIX: 增加到15页，确保包含完整目录
        toc_pages, toc_text = self.extract_toc_pages(file_path, max_toc_pages=15)

        # 步骤2: 识别章节格式
        toc_info = self.identify_chapter_patterns(toc_text)

        # 步骤3: 提取所有页面内容
        print("📖 正在提取全部页面内容...")
        try:
            with fitz.open(file_path) as doc:
                all_pages = []
                toc_page_nums = set()  # 记录目录页的页码

                for page_num in range(len(doc)):
                    page = doc[page_num]
                    text = page.get_text().strip()

                    if text:
                        # 检查这一页是否是目录页
                        is_toc = any(keyword in text for keyword in
                                 ['目录', 'Contents', '目　录'])

                        if is_toc and page_num < 5:
                            toc_page_nums.add(page_num)
                            print(f"   📋 第 {page_num + 1} 页标记为目录页")
                        else:
                            # 这是正文内容
                            all_pages.append({
                                'page': page_num + 1,
                                'content': text
                            })

                print(f"✅ 提取完成: {len(all_pages)} 页正文，{len(toc_page_nums)} 页目录")

                # 步骤4: 合并正文内容（不包含目录页）
                full_content = "\n\n".join([
                    f"--- 第{p['page']}页 ---\n{p['content']}"
                    for p in all_pages
                ])

                # 步骤5: 创建 Langchain 文档
                base_metadata = metadata or {}
                documents = [Document(page_content=full_content, metadata=base_metadata)]

                # 步骤6: 切分文档
                print("✂️  正在切分文档...")
                chunks = self.text_splitter.split_documents(documents)

                # 为每个 chunk 添加 ID
                for i, chunk in enumerate(chunks):
                    chunk.metadata.update({
                        'chunk_id': i,
                        'total_chunks': len(chunks),
                        'source_file': base_metadata.get('title', 'unknown')
                    })

                print(f"   切分完成: {len(chunks)} 个 chunks")

                # 步骤7: 生成向量
                print("🧠 正在生成向量...")
                texts = [chunk.page_content for chunk in chunks]
                embeddings = await self.generate_embeddings(texts)

                # 步骤8: 统计信息
                stats = {
                    'total_pages': len(doc),
                    'toc_pages': len(toc_page_nums),
                    'content_pages': len(all_pages),
                    'total_chunks': len(chunks),
                    'total_chars': sum(len(t) for t in texts)
                }

                return {
                    'toc_text': toc_text,  # 纯净的目录文本，用于章节分析
                    'content_texts': [p['content'] for p in all_pages],  # 正文内容
                    'chunks': chunks,
                    'embeddings': embeddings,
                    'texts': texts,
                    'stats': stats,
                    'toc_info': toc_info
                }

        except Exception as e:
            print(f"❌ PDF 处理失败: {str(e)}")
            raise

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """生成文本嵌入向量"""
        try:
            embeddings = []
            batch_size = 25

            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]

                response = TextEmbedding.call(
                    model='text-embedding-v2',
                    input=batch,
                    text_type='document'
                )

                if response.status_code == 200:
                    for emb in response.output['embeddings']:
                        embeddings.append(emb['embedding'])
                else:
                    raise Exception(f"Embedding API 错误: {response.message}")

            return embeddings

        except Exception as e:
            print(f"❌ 向量化失败: {str(e)}")
            raise
