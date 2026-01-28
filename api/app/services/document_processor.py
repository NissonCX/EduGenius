"""
Document Processing Service
处理 PDF/TXT 文档解析、切分、向量化的完整流程
"""
import os
import hashlib
import fitz  # PyMuPDF
from typing import List, Dict, Any, Optional
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
import dashscope
from dashscope import TextEmbedding

from app.core.config import settings


class DocumentProcessor:
    """文档处理器：解析、切分、向量化"""

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

    async def process_pdf(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        处理 PDF 文件

        Args:
            file_path: PDF 文件路径
            metadata: 额外的元数据

        Returns:
            切分后的文档列表
        """
        try:
            # 使用 PyMuPDF 解析 PDF
            doc = fitz.open(file_path)
            text_content = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    text_content.append({
                        'page': page_num + 1,
                        'content': text
                    })

            doc.close()

            # 合并所有页面文本
            full_text = "\n\n".join([
                f"[第{item['page']}页]\n{item['content']}"
                for item in text_content
            ])

            # 创建元数据
            base_metadata = {
                'source': file_path,
                'type': 'pdf',
                'total_pages': len(doc)
            }
            if metadata:
                base_metadata.update(metadata)

            # 创建 Document 对象
            document = Document(page_content=full_text, metadata=base_metadata)

            # 切分文档
            chunks = self.text_splitter.split_documents([document])

            # 为每个 chunk 添加更多信息
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({
                    'chunk_id': i,
                    'total_chunks': len(chunks)
                })

            return chunks

        except Exception as e:
            raise Exception(f"PDF 解析失败: {str(e)}")

    async def process_txt(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        处理 TXT 文件

        Args:
            file_path: TXT 文件路径
            metadata: 额外的元数据

        Returns:
            切分后的文档列表
        """
        try:
            # 使用 LangChain 的 TextLoader
            loader = TextLoader(file_path, encoding='utf-8')
            documents = loader.load()

            # 添加元数据
            base_metadata = {
                'source': file_path,
                'type': 'txt'
            }
            if metadata:
                base_metadata.update(metadata)

            for doc in documents:
                doc.metadata.update(base_metadata)

            # 切分文档
            chunks = self.text_splitter.split_documents(documents)

            # 为每个 chunk 添加 ID
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({
                    'chunk_id': i,
                    'total_chunks': len(chunks)
                })

            return chunks

        except Exception as e:
            raise Exception(f"TXT 解析失败: {str(e)}")

    async def generate_embeddings(
        self,
        texts: List[str]
    ) -> List[List[float]]:
        """
        使用 DashScope 生成文本嵌入向量

        Args:
            texts: 文本列表

        Returns:
            嵌入向量列表
        """
        try:
            # DashScope Text Embedding API
            # 使用 text-embedding-v2 模型
            embeddings = []

            # 批量处理（每次最多 25 个文本）
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
            raise Exception(f"生成嵌入向量失败: {str(e)}")

    async def process_document(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        完整的文档处理流程：解析 -> 切分 -> 向量化

        Args:
            file_path: 文件路径
            metadata: 额外的元数据

        Returns:
            处理结果，包含 chunks、embeddings、统计信息
        """
        # 判断文件类型
        file_ext = Path(file_path).suffix.lower()

        # 解析文档
        if file_ext == '.pdf':
            chunks = await self.process_pdf(file_path, metadata)
        elif file_ext == '.txt':
            chunks = await self.process_txt(file_path, metadata)
        else:
            raise ValueError(f"不支持的文件类型: {file_ext}")

        # 提取文本用于向量化
        texts = [chunk.page_content for chunk in chunks]

        # 生成嵌入向量
        embeddings = await self.generate_embeddings(texts)

        # 统计信息
        stats = {
            'total_chunks': len(chunks),
            'total_characters': sum(len(text) for text in texts),
            'avg_chunk_length': sum(len(text) for text in texts) / len(texts) if texts else 0,
            'embedding_dimension': len(embeddings[0]) if embeddings else 0
        }

        return {
            'chunks': chunks,
            'embeddings': embeddings,
            'stats': stats,
            'texts': texts
        }

    @staticmethod
    def calculate_md5(file_path: str) -> str:
        """计算文件的 MD5 哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()


# 导出函数
async def process_uploaded_document(
    file_path: str,
    title: str,
    user_email: str
) -> Dict[str, Any]:
    """
    处理上传的文档

    Args:
        file_path: 文件路径
        title: 文档标题
        user_email: 用户邮箱

    Returns:
        处理结果
    """
    processor = DocumentProcessor()

    # 计算 MD5
    md5_hash = processor.calculate_md5(file_path)

    # 准备元数据
    metadata = {
        'title': title,
        'user_email': user_email,
        'md5': md5_hash
    }

    # 处理文档
    result = await processor.process_document(file_path, metadata)

    # 添加 MD5 到结果
    result['md5'] = md5_hash

    return result
