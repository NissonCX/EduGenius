"""
统一文档处理器

支持 PDF、TXT、DOCX、PPTX 等多种格式的文档处理
"""
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LangchainDocument
from langchain_community.document_loaders import TextLoader

from app.services.document_extractors import extract_text_from_file, DocumentExtractorFactory
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class UnifiedDocumentProcessor:
    """
    统一文档处理器

    支持 PDF、TXT、DOCX、PPTX 等多种格式
    """

    def __init__(self):
        """初始化处理器"""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
        )

        # 配置 DashScope Embedding（如果需要向量化）
        try:
            import dashscope
            dashscope.api_key = settings.DASHSCOPE_API_KEY
        except Exception as e:
            logger.warning(f"DashScope API key not configured: {e}")

    async def extract_text_from_file(self, file_path: str) -> str:
        """
        从文件提取文本（自动识别格式）

        Args:
            file_path: 文件路径

        Returns:
            str: 提取的文本内容

        Raises:
            ValueError: 不支持的文件类型
            Exception: 提取失败
        """
        logger.info(f"📖 开始提取文本: {file_path}")
        return extract_text_from_file(file_path)

    async def process_document(
        self,
        file_path: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        处理文档（自动识别格式）

        Args:
            file_path: 文件路径
            title: 文档标题
            metadata: 额外的元数据

        Returns:
            包含以下内容的字典:
            - success: 是否成功
            - content: 提取的文本内容
            - chunks: 切分后的文本块
            - num_chunks: 切块数量
            - file_type: 文件类型
            - metadata: 元数据
        """
        try:
            # 1. 提取文件扩展名
            path_obj = Path(file_path)
            file_ext = path_obj.suffix.lstrip('.')
            file_type = file_ext if file_ext else 'unknown'

            logger.info(f"📄 处理文件类型: .{file_type}")

            # 2. 提取文本
            content = await self.extract_text_from_file(file_path)

            if not content or len(content.strip()) < 10:
                raise ValueError("提取的文本内容为空")

            # 3. 创建基础元数据
            base_metadata = {
                'source': file_path,
                'type': file_type,
                'title': title or path_obj.stem
            }
            if metadata:
                base_metadata.update(metadata)

            # 4. 切分文本
            chunks = self.text_splitter.split_text(content)
            logger.info(f"✅ 文档切分完成: {len(chunks)} 个 chunks")

            # 创建 Langchain Document 对象
            langchain_docs = [
                LangchainDocument(page_content=chunk, metadata=base_metadata)
                for chunk in chunks
            ]

            return {
                'success': True,
                'content': content,
                'chunks': langchain_docs,
                'num_chunks': len(langchain_docs),
                'file_type': file_type,
                'metadata': base_metadata
            }

        except ValueError as e:
            logger.error(f"❌ 文档处理失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_type': Path(file_path).suffix.lstrip('.'),
                'content': None,
                'chunks': [],
                'num_chunks': 0
            }
        except Exception as e:
            logger.error(f"❌ 文档处理异常: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'file_type': Path(file_path).suffix.lstrip('.'),
                'content': None,
                'chunks': [],
                'num_chunks': 0
            }

    def get_supported_formats(self) -> List[str]:
        """
        获取支持的文件格式列表

        Returns:
            List[str]: 支持的文件扩展名
        """
        return DocumentExtractorFactory.supported_formats()


# 便捷函数
def create_unified_processor() -> UnifiedDocumentProcessor:
    """
    创建统一文档处理器实例

    Returns:
        UnifiedDocumentProcessor: 处理器实例
    """
    return UnifiedDocumentProcessor()
