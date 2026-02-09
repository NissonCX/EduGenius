"""
带缓存的 CRUD 操作模块

提供常用数据查询的缓存版本，减少数据库访问
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.models.document import Document, Progress, User
from app.core.cache import (
    cache_get,
    cache_set,
    cache_delete,
    cache_delete_pattern,
    CacheKeyBuilder
)

logger = logging.getLogger(__name__)


# ============ 文档相关缓存查询 ============

async def get_document_cached(
    document_id: int,
    db: AsyncSession
) -> Optional[Document]:
    """
    获取文档信息（带缓存）

    缓存策略：长期缓存（15分钟），文档元数据很少变化
    """
    # 尝试从缓存获取
    cached = await cache_get(CacheKeyBuilder.DOC_INFO, document_id)
    if cached:
        logger.debug(f"✅ 缓存命中: document_{document_id}")
        # 返回字典而不是 ORM 对象
        return cached

    # 从数据库查询
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if document:
        # 转换为字典并缓存
        doc_dict = {
            "id": document.id,
            "filename": document.filename,
            "title": document.title,
            "file_type": document.file_type,
            "file_size": document.file_size,
            "total_pages": document.total_pages,
            "total_chapters": document.total_chapters,
            "processing_status": document.processing_status,
            "md5_hash": document.md5_hash,
            "uploaded_by": document.uploaded_by,
            "uploaded_at": document.uploaded_at.isoformat() if document.uploaded_at else None,
            "has_text_layer": document.has_text_layer,
            "ocr_confidence": document.ocr_confidence
        }
        await cache_set(
            CacheKeyBuilder.DOC_INFO,
            doc_dict,
            ttl='very_long',  # 15分钟
            document_id=document_id
        )
        return doc_dict

    return None


async def get_documents_list_cached(
    user_id: int,
    db: AsyncSession
) -> List[Dict[str, Any]]:
    """
    获取用户文档列表（带缓存）

    缓存策略：中等缓存（5分钟），列表可能因上传/删除而变化
    """
    # 尝试从缓存获取
    cached = await cache_get(CacheKeyBuilder.DOC_CHAPTERS, user_id)
    if cached:
        logger.debug(f"✅ 缓存命中: documents_list_user_{user_id}")
        return cached

    # 从数据库查询
    result = await db.execute(
        select(Document).where(
            Document.uploaded_by == user_id
        ).order_by(Document.uploaded_at.desc())
    )
    documents = result.scalars().all()

    # 转换为字典列表
    document_list = []
    for doc in documents:
        document_list.append({
            "id": doc.id,
            "filename": doc.filename,
            "title": doc.title or doc.filename,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "total_pages": doc.total_pages,
            "total_chapters": doc.total_chapters,
            "processing_status": doc.processing_status,
            "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            "md5_hash": doc.md5_hash
        })

    # 缓存结果
    await cache_set(
        CacheKeyBuilder.DOC_CHAPTERS,
        document_list,
        ttl='medium',  # 5分钟
        user_id=user_id
    )

    return document_list


async def invalidate_document_cache(document_id: int, user_id: int = None):
    """
    清除文档相关的缓存

    Args:
        document_id: 文档ID
        user_id: 用户ID（可选，用于清除文档列表缓存）
    """
    # 清除文档信息缓存
    await cache_delete(CacheKeyBuilder.DOC_INFO, document_id)

    # 清除章节相关缓存
    await cache_delete_pattern(f"{CacheKeyBuilder.DOC_CHAPTERS}:{document_id}")
    await cache_delete_pattern(f"{CacheKeyBuilder.CHAPTER_INFO}:{document_id}")
    await cache_delete_pattern(f"{CacheKeyBuilder.CHAPTER_CONTENT}:{document_id}")

    # 如果提供了用户ID，清除用户的文档列表缓存
    if user_id:
        await cache_delete_pattern(f"{CacheKeyBuilder.DOC_CHAPTERS}:{user_id}")

    logger.info(f"🗑️ 已清除文档 {document_id} 的所有缓存")


# ============ 用户相关缓存查询 ============

async def get_user_info_cached(
    user_id: int,
    db: AsyncSession
) -> Optional[Dict[str, Any]]:
    """
    获取用户信息（带缓存）

    缓存策略：长期缓存（15分钟），用户信息很少变化
    """
    # 尝试从缓存获取
    cached = await cache_get(CacheKeyBuilder.USER_INFO, user_id)
    if cached:
        logger.debug(f"✅ 缓存命中: user_{user_id}")
        return cached

    # 从数据库查询
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user:
        # 转换为字典并缓存
        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "teaching_style": user.teaching_style,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
        await cache_set(
            CacheKeyBuilder.USER_INFO,
            user_dict,
            ttl='very_long',  # 15分钟
            user_id=user_id
        )
        return user_dict

    return None


async def invalidate_user_cache(user_id: int):
    """
    清除用户相关的缓存

    Args:
        user_id: 用户ID
    """
    # 清除用户信息缓存
    await cache_delete(CacheKeyBuilder.USER_INFO, user_id)

    # 清除用户进度和对话缓存
    await cache_delete_pattern(f"{CacheKeyBuilder.USER_PROGRESS}:{user_id}")
    await cache_delete_pattern(f"{CacheKeyBuilder.USER_HISTORY}:{user_id}")

    logger.info(f"🗑️ 已清除用户 {user_id} 的所有缓存")


# ============ 进度相关缓存查询 ============

async def get_user_progress_cached(
    user_id: int,
    document_id: int,
    db: AsyncSession
) -> List[Dict[str, Any]]:
    """
    获取用户在文档中的进度（带缓存）

    缓存策略：短期缓存（1分钟），进度数据频繁变化
    """
    # 尝试从缓存获取
    cached = await cache_get(CacheKeyBuilder.USER_PROGRESS, user_id, document_id)
    if cached:
        logger.debug(f"✅ 缓存命中: progress_user_{user_id}_doc_{document_id}")
        return cached

    # 从数据库查询
    result = await db.execute(
        select(Progress).where(
            Progress.user_id == user_id,
            Progress.document_id == document_id
        )
    )
    progress_records = result.scalars().all()

    # 转换为字典列表
    progress_list = []
    for p in progress_records:
        progress_list.append({
            "id": p.id,
            "chapter_number": p.chapter_number,
            "chapter_title": p.chapter_title,
            "completion_percentage": p.completion_percentage,
            "time_spent_minutes": p.time_spent_minutes,
            "is_locked": p.is_locked,
            "quiz_score": p.quiz_score
        })

    # 缓存结果（短时间）
    await cache_set(
        CacheKeyBuilder.USER_PROGRESS,
        progress_list,
        ttl='short',  # 1分钟
        user_id=user_id,
        document_id=document_id
    )

    return progress_list


async def invalidate_progress_cache(user_id: int, document_id: int = None):
    """
    清除进度相关的缓存

    Args:
        user_id: 用户ID
        document_id: 文档ID（可选）
    """
    if document_id:
        # 清除特定文档的进度缓存
        await cache_delete(CacheKeyBuilder.USER_PROGRESS, user_id, document_id)
        await cache_delete_pattern(f"{CacheKeyBuilder.CHAPTER_PROGRESS}:{user_id}:{document_id}")
    else:
        # 清除用户所有进度缓存
        await cache_delete_pattern(f"{CacheKeyBuilder.USER_PROGRESS}:{user_id}")
        await cache_delete_pattern(f"{CacheKeyBuilder.CHAPTER_PROGRESS}:{user_id}")

    logger.info(f"🗑️ 已清除用户 {user_id} 的进度缓存")


# ============ 章节内容缓存（静态数据）============

async def get_chapter_content_cached(
    document_id: int,
    chapter_number: int,
    db: AsyncSession
) -> Optional[str]:
    """
    获取章节内容（带缓存）

    缓存策略：长期缓存（15分钟），章节内容是静态的
    """
    # 尝试从缓存获取
    cached = await cache_get(CacheKeyBuilder.CHAPTER_CONTENT, document_id, chapter_number)
    if cached:
        logger.debug(f"✅ 缓存命中: chapter_content_doc_{document_id}_ch_{chapter_number}")
        return cached

    # 从 ChromaDB 获取内容
    from app.core.chroma import get_document_collection
    from app.models.document import Document
    import re

    # 获取文档信息
    doc_result = await db.execute(select(Document).where(Document.id == document_id))
    document = doc_result.scalar_one_or_none()

    if not document or not document.md5_hash:
        return None

    # 从 ChromaDB 获取内容
    collection = get_document_collection(document.md5_hash)
    if not collection or collection.count() == 0:
        return None

    # 获取所有 chunks
    results = collection.get()
    if results and results['documents']:
        full_text = "\n\n".join(results['documents'])

        # 提取特定章节内容
        chapter_patterns = [
            rf'第{chapter_number}章',
            rf'第\s*{chapter_number}\s*章',
            rf'Chapter\s*{chapter_number}',
        ]

        chapter_start = -1
        for pattern in chapter_patterns:
            match = re.search(pattern, full_text)
            if match:
                chapter_start = match.start()
                break

        if chapter_start >= 0:
            # 找下一章开始位置
            next_chapter_patterns = [
                rf'第{chapter_number + 1}章',
                rf'第\s*{chapter_number + 1}\s*章',
                rf'Chapter\s*{chapter_number + 1}',
            ]

            chapter_end = len(full_text)
            for pattern in next_chapter_patterns:
                match = re.search(pattern, full_text[chapter_start:])
                if match:
                    chapter_end = chapter_start + match.start()
                    break

            chapter_content = full_text[chapter_start:chapter_end].strip()
        else:
            chapter_content = full_text

        # 限制长度
        if len(chapter_content) > 15000:
            chapter_content = chapter_content[:15000] + "\n\n(内容过长，已截断)"

        # 缓存内容
        await cache_set(
            CacheKeyBuilder.CHAPTER_CONTENT,
            chapter_content,
            ttl='very_long',  # 15分钟
            document_id=document_id,
            chapter_number=chapter_number
        )

        return chapter_content

    return None
