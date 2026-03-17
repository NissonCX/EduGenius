"""
混合文档处理器 - 支持文本提取和OCR双路径

根据PDF的文本层情况，自动选择：
- Fast Path: 直接文本提取（有文本层）
- OCR Path: PaddleOCR识别（无/少文本层）
"""
import asyncio
import time
from typing import Dict, Any, Optional, Callable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.ocr_engine import get_ocr_engine
from app.utils.pdf_validator import validate_pdf_before_upload
from app.services.document_processor import DocumentProcessor
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class HybridDocumentProcessor:
    """混合文档处理器"""

    def __init__(self):
        self.ocr_engine = get_ocr_engine()
        self.text_processor = DocumentProcessor()

        # 配置阈值
        self.TEXT_RATIO_THRESHOLD = 0.1  # 文本页占比阈值
        self.OCR_CONFIDENCE_THRESHOLD = 0.6  # OCR 置信度阈值

    async def process_document(
        self,
        file_path: str,
        document_id: int,
        user_id: int,
        title: str,
        db: AsyncSession,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        混合处理文档

        Args:
            file_path: 文件路径
            document_id: 文档ID
            user_id: 用户ID
            title: 文档标题
            db: 数据库会话
            progress_callback: 进度回调 callback(stage, current, total)
                              stage: 'detecting' | 'extracting' | 'ocr' | 'vectorizing' | 'completed'

        Returns:
            {
                'success': bool,
                'path': 'fast' | 'ocr',
                'text_ratio': float,
                'ocr_confidence': float,
                'processing_time': float,
                'chunks': int,
                'message': str
            }
        """
        import time
        start_time = time.time()

        try:
            # ========== 阶段1: 检测 ==========
            if progress_callback:
                progress_callback('detecting', 0, 1)

            logger.info("="*60)
            logger.info("🔍 阶段 1/4: 检测 PDF 类型")
            logger.info("="*60)

            validation = validate_pdf_before_upload(file_path)

            logger.info(
                f"📊 检测结果: "
                f"总页数={validation['total_pages']}, "
                f"文本页={validation['text_pages']}, "
                f"文本占比={validation['text_ratio']:.1%}, "
                f"是否扫描版={'是' if validation['is_scan'] else '否'}"
            )

            # 更新数据库：记录检测结果
            await self._update_document_status(
                db, document_id,
                has_text_layer=not validation['is_scan'],
                current_page=0,
                total_pages=validation['total_pages']
            )

            # ========== 路径选择 ==========
            if validation['text_ratio'] >= self.TEXT_RATIO_THRESHOLD:
                # ✅ Fast Path: 有足够文本层
                return await self._fast_path(
                    file_path, document_id, user_id, title, db,
                    validation, progress_callback, start_time
                )
            else:
                # ⏱️ OCR Path: 需要OCR处理
                return await self._ocr_path(
                    file_path, document_id, user_id, title, db,
                    validation, progress_callback, start_time
                )

        except Exception as e:
            logger.error(f"❌ 文档处理失败: {e}", exc_info=True)

            # 更新状态为失败
            await self._update_document_status(
                db, document_id,
                processing_status='failed'
            )

            return {
                'success': False,
                'error': str(e),
                'message': f'文档处理失败: {str(e)}'
            }

    async def _fast_path(
        self,
        file_path: str,
        document_id: int,
        user_id: int,
        title: str,
        db: AsyncSession,
        validation: Dict[str, Any],
        progress_callback: Optional[Callable],
        start_time: float
    ) -> Dict[str, Any]:
        """快速路径：直接提取文本"""

        logger.info(f"✅ 选择快速路径（Fast Path）：PDF 有 {validation['text_ratio']:.1%} 的页面包含文本层")

        try:
            # ========== 阶段2: 提取文本 ==========
            if progress_callback:
                progress_callback('extracting', 1, 3)

            logger.info("📖 阶段 2/4: 提取文本（快速路径）")

            # 使用现有的处理器
            from app.services.document_processor import process_uploaded_document
            result = await process_uploaded_document(
                file_path=file_path,
                title=title,
                user_email=""  # 这个参数暂时不用
            )

            # ========== 阶段3: 提取目录并划分章节 ==========
            if progress_callback:
                progress_callback('extracting_toc', 2, 4)

            logger.info("📚 阶段 3/4: 提取目录并划分章节")

            # 提取目录（使用TextbookParser）
            toc_text = ""
            try:
                from app.core.textbook_parser import TextbookParser
                parser = TextbookParser()

                parse_result = await parser.parse_textbook(file_path, db)
                toc_text = parse_result.get('toc_text', '')

                source = parse_result.get('source', 'unknown')
                pages = parse_result.get('pages', [])

                logger.info(
                    f"   目录提取完成: "
                    f"来源={source}, "
                    f"页码={pages}, "
                    f"文本长度={len(toc_text)}字符"
                )
            except Exception as e:
                logger.warning(f"   ⚠️  目录提取失败: {e}，使用文本前3个chunks")
                # Fallback: 使用前3个chunks
                toc_text = "\n\n".join([c.page_content for c in result.get('chunks', [])[:3]])

            # 划分章节（使用改进版提取器）
            chapters_count = 0
            try:
                from app.services.improved_chapter_extractor import ImprovedChapterExtractor

                extractor = ImprovedChapterExtractor()

                if toc_text:
                    logger.info(f"   开始智能提取章节，目录文本长度: {len(toc_text)} 字符")

                    # 🔧 FIX: 使用直接文本提取方法，不需要页面检测
                    chapters = await extractor.extract_chapters_from_text(
                        toc_text=toc_text,
                        document_id=document_id,
                        user_id=user_id,
                        db=db
                    )

                    chapters_count = len(chapters)
                    logger.info(f"   ✅ 成功划分 {chapters_count} 个章节")
                else:
                    logger.warning("   ⚠️  没有目录文本，跳过章节划分")

            except Exception as e:
                logger.error(f"   ❌ 章节划分失败: {e}", exc_info=True)

            # ========== 阶段4: 完成 ==========
            if progress_callback:
                progress_callback('completed', 4, 4)

            logger.info("🧠 阶段 4/4: 向量化并存储")

            # 向量化已经在 process_uploaded_document 中完成
            chunks = result.get('chunks', [])

            processing_time = time.time() - start_time

            # 更新状态（包括章节数）
            await self._update_document_status(
                db, document_id,
                processing_status='completed',
                ocr_confidence=1.0,  # 文本提取的置信度为100%
                total_chapters=chapters_count  # 更新章节数
            )

            logger.info(
                f"✅ 处理完成（快速路径）："
                f"耗时={processing_time:.1f}秒, "
                f"Chunks={len(chunks)}"
            )

            return {
                'success': True,
                'path': 'fast',
                'text_ratio': validation['text_ratio'],
                'ocr_confidence': 1.0,
                'processing_time': processing_time,
                'chunks': len(chunks),
                'message': f'✅ 文档处理完成（快速路径），耗时 {processing_time:.1f}秒'
            }

        except Exception as e:
            await self._update_document_status(
                db, document_id,
                processing_status='failed'
            )
            raise

    async def _ocr_path(
        self,
        file_path: str,
        document_id: int,
        user_id: int,
        title: str,
        db: AsyncSession,
        validation: Dict[str, Any],
        progress_callback: Optional[Callable],
        start_time: float
    ) -> Dict[str, Any]:
        """
        OCR路径：智能处理扫描版 PDF

        三步走策略：
        1. 先尝试提取 PDF 书签（不需要 OCR！）
        2. 如果没有书签，启发式 OCR 前 60 页并智能筛选目录页
        3. 用 LLM 划分章节

        这样最多只需要 OCR 60 页，而不是整本书 424 页
        """

        logger.info(f"⏱️  选择 OCR 路径（OCR Path）：扫描版 PDF，智能提取目录")

        try:
            # 更新状态为处理中
            await self._update_document_status(
                db, document_id,
                processing_status='ocr_processing',
                total_pages=validation['total_pages']
            )

            # ========== 第一步：尝试提取 PDF 书签（不需要 OCR！）==========
            logger.info("📚 第一步：尝试提取 PDF 书签...")

            toc_text = ""
            toc_source = "unknown"
            ocr_confidence = 0.0

            try:
                import fitz
                doc = fitz.open(file_path)
                toc = doc.get_toc()

                if toc and len(toc) > 0:
                    logger.info(f"   ✅ 找到 {len(toc)} 个书签！不需要 OCR")

                    # 构建目录文本
                    toc_parts = []
                    for level, title, page_num in toc:
                        indent = "  " * (level - 1)
                        toc_parts.append(f"{indent}{'•' * level} {title} (第{page_num}页)")

                    toc_text = "\n".join(toc_parts)
                    toc_source = "bookmark"
                    ocr_confidence = 1.0  # 书签不需要 OCR，置信度为 100%
                    doc.close()
                else:
                    logger.info("   ⚠️  没有书签，需要 OCR 提取目录")
                    doc.close()

            except Exception as e:
                logger.warning(f"   ⚠️  书签提取失败: {e}，将使用 OCR")

            # ========== 第二步：如果没有书签，启发式 OCR 前 60 页 ==========
            if not toc_text:
                MAX_SCAN_PAGES = 60
                pages_to_ocr = list(range(1, min(MAX_SCAN_PAGES + 1, validation['total_pages'] + 1)))

                logger.info(f"🔬 第二步：启发式 OCR 识别前 {len(pages_to_ocr)} 页...")

                if progress_callback:
                    progress_callback('ocr', 0, len(pages_to_ocr))

                # 更新总页数
                await self._update_document_status(
                    db, document_id,
                    total_pages=len(pages_to_ocr)
                )

                # 进度回调
                def ocr_progress(current: int, total: int, message: str):
                    logger.info(f"   {message}")
                    if progress_callback:
                        progress_callback('ocr', current, len(pages_to_ocr))

                    # 每处理 5 页更新一次数据库
                    if current % 5 == 0:
                        try:
                            loop = asyncio.get_running_loop()
                            loop.call_soon_threadsafe(
                                lambda: asyncio.create_task(
                                    self._update_document_status(
                                        db, document_id,
                                        current_page=current
                                    )
                                )
                            )
                        except RuntimeError as e:
                            # 在某些情况下（如事件循环已关闭）可能抛出 RuntimeError
                            # 记录日志但不中断处理
                            logger.debug(
                                f"无法更新文档进度（可能事件循环已关闭）: "
                                f"document_id={document_id}, page={current}, error={e}"
                            )

                # 🔧 FIX: 使用 asyncio.to_thread 将同步 OCR 移到线程池
                # 这样其他 API 请求不会被阻塞
                import asyncio

                ocr_result = await asyncio.to_thread(
                    self.ocr_engine.process_pdf,
                    pdf_path=file_path,
                    pages=pages_to_ocr,
                    progress_callback=ocr_progress
                )

                if not ocr_result['success']:
                    raise Exception(f"OCR 处理失败: {ocr_result['errors']}")

                ocr_confidence = ocr_result['avg_confidence']
                logger.info(f"   ✅ OCR 完成，识别了 {len(ocr_result['pages'])} 页，置信度 {ocr_confidence:.1%}")

                # ========== 智能筛选：找出最可能是目录的页 ==========
                logger.info("🔍 第三步：智能筛选目录页...")

                # 导入 TextbookParser 的评分逻辑
                from app.core.textbook_parser import TextbookParser
                parser = TextbookParser()

                # 🔧 FIX: 对每一页评分，使用与Fast Path相同的逻辑
                page_scores = []
                for page_data in ocr_result['pages']:
                    text = page_data['text']
                    page_num = page_data['page_num']

                    if text.strip():
                        score = parser._calculate_page_score(text, page_num - 1)
                        # 保存所有页面信息，包括文本
                        page_scores.append({
                            'page': page_num,
                            'score': score,
                            'text': text,
                            'char_count': len(text)
                        })

                        # 显示前10页的分数
                        if page_num <= 10:
                            status = "✅" if score > 20 else "  "
                            logger.info(f"   {status} 第 {page_num:2} 页: {score:3} 分 | {len(text):4} 字符")

                if page_scores:
                    # 🔧 FIX: 使用修复后的连续性检查逻辑
                    # 将数据转换为 _select_best_pages 需要的格式
                    best_pages = parser._select_best_pages(page_scores)

                    logger.info(f"   ✅ 选定 {len(best_pages)} 个目录页: {[p['page'] for p in best_pages]}")

                    # 合并文本
                    toc_text = "\n\n".join([
                        f"--- 第{p['page']}页 ---\n{p['text']}"
                        for p in best_pages
                    ])
                    toc_source = "ocr_scan"

                    # 显示选择结果的详细信息
                    logger.info(f"   📊 目录文本总长度: {len(toc_text)} 字符")
                else:
                    # Fallback: 使用所有 OCR 文本
                    logger.warning("   ⚠️  未找到明显目录页，使用所有 OCR 文本")
                    toc_text = ocr_result['full_text']
                    toc_source = "ocr_fallback"

            # ========== 第三步：使用改进版章节提取器 ==========
            if progress_callback:
                progress_callback('processing', 1, 3)

            logger.info(f"🧠 第三步：使用改进版章节提取器（目录来源: {toc_source}）")
            logger.info(f"   目录文本长度: {len(toc_text)} 字符")

            chapters_count = 0
            try:
                from app.services.improved_chapter_extractor import ImprovedChapterExtractor

                extractor = ImprovedChapterExtractor()

                logger.info("📚 开始智能提取章节...")

                # 🔧 FIX: OCR路径已经有选择好的目录文本，直接使用 extract_chapters_from_text
                if toc_text and len(toc_text) > 100:
                    logger.info(f"   使用预选的目录文本进行章节提取")
                    chapters = await extractor.extract_chapters_from_text(
                        toc_text=toc_text,
                        document_id=document_id,
                        user_id=user_id,
                        db=db
                    )
                else:
                    # Fallback: 如果没有足够的目录文本，尝试从OCR结果重新提取
                    logger.warning(f"   ⚠️  目录文本太短（{len(toc_text)}字符），尝试从OCR结果重新提取")
                    chapters = await extractor.extract_chapters(
                        ocr_result=ocr_result,
                        file_path=file_path,
                        document_id=document_id,
                        user_id=user_id,
                        db=db
                    )

                chapters_count = len(chapters) if chapters else 0
                logger.info(f"✅ 成功提取 {chapters_count} 个章节")

                # 打印章节列表
                if chapters:
                    logger.info("📚 提取的章节列表:")
                    for ch in chapters:
                        subs = ch.get('subsections', [])
                        logger.info(f"   第{ch['chapter_number']}章: {ch['chapter_title']} ({len(subs)}个小节)")

            except Exception as e:
                logger.warning(f"⚠️  章节提取失败: {e}", exc_info=True)
                import traceback
                traceback.print_exc()

            processing_time = time.time() - start_time

            # ========== 完成 ==========
            if progress_callback:
                progress_callback('completed', 3, 3)

            # 更新状态
            await self._update_document_status(
                db, document_id,
                processing_status='completed',
                ocr_confidence=ocr_confidence,
                total_chapters=chapters_count
            )

            logger.info(
                f"✅ OCR 处理完成: "
                f"耗时={processing_time:.1f}秒, "
                f"目录来源={toc_source}, "
                f"置信度={ocr_confidence:.1%}, "
                f"章节数={chapters_count}"
            )

            return {
                'success': True,
                'path': 'ocr',
                'text_ratio': validation['text_ratio'],
                'ocr_confidence': ocr_confidence,
                'processing_time': processing_time,
                'chunks': 0,
                'toc_source': toc_source,
                'message': f'✅ 处理完成（{toc_source}），{chapters_count} 个章节，耗时 {processing_time:.1f}秒'
            }

        except Exception as e:
            logger.error(f"❌ OCR 处理失败: {e}", exc_info=True)
            await self._update_document_status(
                db, document_id,
                processing_status='failed'
            )
            raise

    async def _update_document_status(
        self,
        db: AsyncSession,
        document_id: int,
        processing_status: Optional[str] = None,
        has_text_layer: Optional[bool] = None,
        ocr_confidence: Optional[float] = None,
        current_page: Optional[int] = None,
        total_pages: Optional[int] = None,
        total_chapters: Optional[int] = None
    ):
        """更新文档处理状态"""
        updates = []
        params = {'document_id': document_id}

        if processing_status is not None:
            updates.append('processing_status = :processing_status')
            params['processing_status'] = processing_status

        if has_text_layer is not None:
            updates.append('has_text_layer = :has_text_layer')
            params['has_text_layer'] = has_text_layer

        if ocr_confidence is not None:
            updates.append('ocr_confidence = :ocr_confidence')
            params['ocr_confidence'] = ocr_confidence

        if current_page is not None:
            updates.append('current_page = :current_page')
            params['current_page'] = current_page

        if total_pages is not None:
            updates.append('total_pages = :total_pages')
            params['total_pages'] = total_pages

        if total_chapters is not None:
            updates.append('total_chapters = :total_chapters')
            params['total_chapters'] = total_chapters

        if updates:
            query = text(f"""
                UPDATE documents
                SET {', '.join(updates)}
                WHERE id = :document_id
            """)
            await db.execute(query, params)
            await db.commit()
