"""
混合文档处理器 - 支持文本提取和OCR双路径

根据PDF的文本层情况，自动选择：
- Fast Path: 直接文本提取（有文本层）
- OCR Path: PaddleOCR识别（无/少文本层）
"""
import asyncio
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

            # ========== 阶段3: 向量化 ==========
            if progress_callback:
                progress_callback('vectorizing', 2, 3)

            logger.info("🧠 阶段 3/4: 向量化并存储")

            # 向量化已经在 process_uploaded_document 中完成
            chunks = result.get('chunks', [])

            # ========== 阶段4: 完成 ==========
            if progress_callback:
                progress_callback('completed', 3, 3)

            processing_time = time.time() - start_time

            # 更新状态
            await self._update_document_status(
                db, document_id,
                processing_status='completed',
                ocr_confidence=1.0  # 文本提取的置信度为100%
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
        """OCR路径：使用PaddleOCR识别"""

        logger.info(f"⏱️  选择 OCR 路径（OCR Path）：只有 {validation['text_ratio']:.1%} 的页面有文本层")

        try:
            # 更新状态为 OCR 处理中
            await self._update_document_status(
                db, document_id,
                processing_status='ocr_processing'
            )

            # ========== 阶段2: OCR识别 ==========
            if progress_callback:
                progress_callback('ocr', 0, validation['total_pages'])

            logger.info("🔬 阶段 2/4: OCR 文字识别")

            # 定义进度回调
            def ocr_progress(current: int, total: int, message: str):
                logger.info(f"   {message}")
                if progress_callback:
                    progress_callback('ocr', current, total)

                # 更新数据库进度
                asyncio.create_task(self._update_document_status(
                    db, document_id,
                    current_page=current
                ))

            # 执行 OCR
            ocr_result = self.ocr_engine.process_pdf(
                file_path=file_path,
                progress_callback=ocr_progress
            )

            if not ocr_result['success']:
                raise Exception(f"OCR 处理失败: {ocr_result['errors']}")

            # 检查置信度
            if ocr_result['avg_confidence'] < self.OCR_CONFIDENCE_THRESHOLD:
                raise Exception(
                    f"OCR 识别质量过低（置信度: {ocr_result['avg_confidence']:.1%}），"
                    f"请上传更清晰的扫描件"
                )

            # ========== 阶段3: 文本后处理 ==========
            if progress_callback:
                progress_callback('processing', 1, 3)

            logger.info("📝 阶段 3/4: 文本后处理")

            # 使用OCR提取的文本
            extracted_text = ocr_result['full_text']

            logger.info(f"   提取文本长度: {len(extracted_text)} 字符")

            # TODO: 这里可以进行文本后处理
            # - 格式校正
            # - 段落重组
            # - 特殊字符修复

            # ========== 阶段4: 向量化 ==========
            if progress_callback:
                progress_callback('vectorizing', 2, 3)

            logger.info("🧠 阶段 4/4: 向量化并提取章节")

            # 使用OCR提取的文本进行章节划分
            try:
                from app.services.chapter_divider_enhanced import EnhancedChapterDivider

                divider = EnhancedChapterDivider()

                logger.info("📚 开始从OCR文本中提取章节...")

                # 提取章节
                chapters = await divider.divide_document_into_chapters(
                    document_id=document_id,
                    user_id=user_id,
                    document_text=ocr_result['full_text'],
                    db=db
                )

                logger.info(f"✅ 成功提取 {len(chapters)} 个章节")

            except Exception as e:
                logger.warning(f"⚠️  章节提取失败: {e}", exc_info=True)

            processing_time = time.time() - start_time

            # ========== 完成 ==========
            if progress_callback:
                progress_callback('completed', 3, 3)

            # 更新状态
            await self._update_document_status(
                db, document_id,
                processing_status='completed',
                ocr_confidence=ocr_result['avg_confidence']
            )

            logger.info(
                f"✅ OCR 处理完成: "
                f"耗时={processing_time:.1f}秒, "
                f"平均置信度={ocr_result['avg_confidence']:.1%}, "
                f"识别页数={ocr_result['processed_pages']}/{ocr_result['total_pages']}"
            )

            return {
                'success': True,
                'path': 'ocr',
                'text_ratio': validation['text_ratio'],
                'ocr_confidence': ocr_result['avg_confidence'],
                'processing_time': processing_time,
                'chunks': 0,  # TODO: 实际chunk数量
                'message': f'✅ OCR识别完成，置信度 {ocr_result["avg_confidence"]:.1%}，耗时 {processing_time:.1f}秒'
            }

        except Exception as e:
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
        total_pages: Optional[int] = None
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

        if updates:
            query = text(f"""
                UPDATE documents
                SET {', '.join(updates)}
                WHERE id = :document_id
            """)
            await db.execute(query, params)
            await db.commit()
