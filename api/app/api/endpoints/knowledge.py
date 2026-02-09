"""
知识图谱 API 端点

提供基于文档章节和用户学习进度的知识图谱数据
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel

from app.db.database import get_db
from app.models.document import User, Document, Progress
from app.core.security import get_current_user
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


# ============ 响应模型 ============
class KnowledgeNode(BaseModel):
    """知识图谱节点"""
    id: str
    label: str
    status: Literal['completed', 'in-progress', 'locked']
    category: str
    value: int
    progress: Optional[int] = None
    time_spent: Optional[int] = None
    description: Optional[str] = None
    chapter_number: Optional[int] = None


class KnowledgeLink(BaseModel):
    """知识图谱连线"""
    source: str
    target: str
    strength: float


class KnowledgeGraphResponse(BaseModel):
    """知识图谱响应"""
    nodes: List[KnowledgeNode]
    links: List[KnowledgeLink]
    metadata: Dict[str, Any]


# ============ 辅助函数 ============
async def get_document_knowledge_nodes(
    document_id: int,
    user_id: int,
    db: AsyncSession
) -> List[KnowledgeNode]:
    """
    获取文档的知识节点

    基于：
    1. 章节结构
    2. 用户学习进度
    3. 章节锁定状态
    """
    # 获取文档信息
    doc_result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = doc_result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 获取所有章节进度
    progress_result = await db.execute(
        select(Progress).where(
            and_(
                Progress.user_id == user_id,
                Progress.document_id == document_id
            )
        ).order_by(Progress.chapter_number)
    )
    progress_records = progress_result.scalars().all()

    # 构建进度映射
    progress_map = {p.chapter_number: p for p in progress_records}

    nodes = []

    # 为每个章节创建节点
    for chapter_num in range(1, document.total_chapters + 1):
        progress = progress_map.get(chapter_num)

        if progress:
            # 有进度记录
            if progress.completion_percentage >= 80:
                status = 'completed'
            elif progress.completion_percentage >= 20:
                status = 'in-progress'
            else:
                status = 'locked'
        else:
            # 无进度记录，检查是否是第一章（第一章默认解锁）
            if chapter_num == 1:
                status = 'locked'  # 未开始但可访问
            else:
                # 检查前一章的完成度
                prev_progress = progress_map.get(chapter_num - 1)
                if prev_progress and prev_progress.completion_percentage >= 70:
                    status = 'locked'  # 可访问但未开始
                else:
                    status = 'locked'  # 未解锁

        # 确定节点分类
        if chapter_num <= document.total_chapters * 0.3:
            category = 'basic'
        elif chapter_num <= document.total_chapters * 0.7:
            category = 'intermediate'
        else:
            category = 'advanced'

        # 确定节点大小（根据章节内容权重）
        if progress and progress.quiz_score:
            value = max(1, min(3, int(progress.quiz_score / 40)))
        else:
            value = 1

        node = KnowledgeNode(
            id=f"doc_{document_id}_ch_{chapter_num}",
            label=progress.chapter_title if progress else f"第{chapter_num}章",
            status=status,
            category=category,
            value=value,
            progress=int(progress.completion_percentage) if progress else 0,
            time_spent=int(progress.time_spent_minutes) if progress else 0,
            description=f"第{chapter_num}章 - {progress.chapter_title if progress else ''}",
            chapter_number=chapter_num
        )
        nodes.append(node)

    return nodes


async def calculate_knowledge_links(
    nodes: List[KnowledgeNode],
    document_id: int,
    db: AsyncSession
) -> List[KnowledgeLink]:
    """
    计算知识节点之间的关联关系

    基于：
    1. 章节顺序关系
    2. 前置依赖关系
    3. 主题相关性
    """
    links = []

    # 基于章节顺序创建连线
    for i in range(len(nodes) - 1):
        current = nodes[i]
        next_node = nodes[i + 1]

        # 计算关联强度
        if current.status == 'completed' and next_node.status in ['in-progress', 'completed']:
            strength = 0.9  # 强关联：当前已完成，下一个正在进行
        elif current.status == 'completed':
            strength = 0.7  # 中等关联：当前已完成，下一个已解锁
        elif current.status == 'in-progress':
            strength = 0.5  # 弱关联：当前正在进行
        else:
            strength = 0.3  # 最弱关联：都未解锁

        links.append(KnowledgeLink(
            source=current.id,
            target=next_node.id,
            strength=strength
        ))

    # 添加跨章节的语义关联（基于章节标题相似度）
    # 这里简化实现：基于章节编号的奇偶关系
    for i in range(0, len(nodes) - 2, 2):
        if i + 2 < len(nodes):
            current = nodes[i]
            skip_node = nodes[i + 2]

            # 只在已解锁的章节之间添加跨章节关联
            if current.status != 'locked' and skip_node.status != 'locked':
                links.append(KnowledgeLink(
                    source=current.id,
                    target=skip_node.id,
                    strength=0.4  # 较弱的跨章节关联
                ))

    return links


async def generate_mastery_stats(
    nodes: List[KnowledgeNode]
) -> Dict[str, Any]:
    """计算掌握度统计"""
    completed = len([n for n in nodes if n.status == 'completed'])
    in_progress = len([n for n in nodes if n.status == 'in-progress'])
    locked = len([n for n in nodes if n.status == 'locked'])

    total_time = sum(n.time_spent or 0 for n in nodes)
    avg_progress = sum(n.progress or 0 for n in nodes) // len(nodes) if nodes else 0

    return {
        'total': len(nodes),
        'completed': completed,
        'in_progress': in_progress,
        'locked': locked,
        'completion_rate': round((completed / len(nodes) * 100) if nodes else 0, 1),
        'total_time_minutes': total_time,
        'avg_progress': avg_progress
    }


# ============ API 端点 ============
@router.get("/graph/{document_id}", response_model=KnowledgeGraphResponse)
async def get_knowledge_graph(
    document_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取文档的知识图谱数据

    返回：
    - nodes: 知识节点列表（章节）
    - links: 节点之间的关联关系
    - metadata: 统计信息
    """
    # 验证用户权限
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="无权访问其他用户的数据")

    # 获取知识节点
    nodes = await get_document_knowledge_nodes(document_id, user_id, db)

    # 计算关联关系
    links = await calculate_knowledge_links(nodes, document_id, db)

    # 生成统计信息
    stats = await generate_mastery_stats(nodes)

    return KnowledgeGraphResponse(
        nodes=nodes,
        links=links,
        metadata={
            'document_id': document_id,
            'user_id': user_id,
            'stats': stats
        }
    )


@router.get("/overview")
async def get_knowledge_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户所有文档的知识图谱概览

    返回用户的整体学习状态，包括：
    - 各文档的完成情况
    - 总学习时间
    - 推荐学习的文档
    """
    # 获取用户所有文档
    from app.crud.document import get_document_by_md5

    doc_result = await db.execute(
        select(Document).where(
            Document.uploaded_by == current_user.id
        ).order_by(Document.uploaded_at.desc())
    )
    documents = doc_result.scalars().all()

    overview = {
        'documents': [],
        'total_stats': {
            'total_documents': len(documents),
            'total_chapters': sum(d.total_chapters or 0 for d in documents),
            'total_time_spent': 0
        },
        'recommendations': []
    }

    for doc in documents:
        # 获取该文档的进度统计
        progress_result = await db.execute(
            select(Progress).where(
                and_(
                    Progress.user_id == current_user.id,
                    Progress.document_id == doc.id
                )
            )
        )
        progress_records = progress_result.scalars().all()

        completed = len([p for p in progress_records if p.completion_percentage >= 80])
        total_time = sum(p.time_spent_minutes for p in progress_records)

        doc_overview = {
            'document_id': doc.id,
            'title': doc.title or doc.filename,
            'total_chapters': doc.total_chapters or 0,
            'completed_chapters': completed,
            'total_time_spent': total_time,
            'completion_rate': round((completed / (doc.total_chapters or 1)) * 100, 1)
        }
        overview['documents'].append(doc_overview)
        overview['total_stats']['total_time_spent'] += total_time

    # 生成推荐：未完成且有时间的文档
    for doc_overview in overview['documents']:
        if doc_overview['completion_rate'] < 100 and doc_overview['total_time_spent'] > 0:
            overview['recommendations'].append({
                'document_id': doc_overview['document_id'],
                'title': doc_overview['title'],
                'reason': f"已完成 {doc_overview['completion_rate']}%，继续学习",
                'priority': 'high' if doc_overview['completion_rate'] > 50 else 'medium'
            })
        elif doc_overview['completed_chapters'] == 0 and doc_overview['total_chapters'] > 0:
            overview['recommendations'].append({
                'document_id': doc_overview['document_id'],
                'title': doc_overview['title'],
                'reason': "尚未开始学习",
                'priority': 'medium'
            })

    return overview


@router.get("/path/{document_id}")
async def get_recommended_learning_path(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取推荐的学习路径

    基于用户当前进度，推荐应该学习的下一章节
    """
    # 获取文档
    doc_result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = doc_result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 获取所有进度
    progress_result = await db.execute(
        select(Progress).where(
            and_(
                Progress.user_id == current_user.id,
                Progress.document_id == document_id
            )
        ).order_by(Progress.chapter_number)
    )
    progress_records = progress_result.scalars().all()

    # 构建进度映射
    progress_map = {p.chapter_number: p for p in progress_records}

    # 找到下一个应该学习的章节
    recommended_chapter = None
    current_chapter = None

    for i in range(1, document.total_chapters + 1):
        progress = progress_map.get(i)

        if progress:
            if progress.completion_percentage < 100:
                recommended_chapter = i
                current_chapter = i
                break
        else:
            # 找到第一个没有进度记录的章节
            recommended_chapter = i
            break

    # 如果所有章节都完成了，推荐复习
    if not recommended_chapter:
        return {
            'action': 'review',
            'message': '恭喜！你已经完成了所有章节',
            'suggested_chapters': [1]  # 从第一章开始复习
        }

    # 检查是否可以开始推荐章节
    can_start = True
    if recommended_chapter > 1:
        prev_progress = progress_map.get(recommended_chapter - 1)
        if not prev_progress or prev_progress.completion_percentage < 70:
            can_start = False
            return {
                'action': 'unlock_prerequisite',
                'message': f'请先完成第{recommended_chapter - 1}章',
                'required_chapter': recommended_chapter - 1,
                'target_chapter': recommended_chapter
            }

    return {
        'action': 'continue',
        'message': f'继续学习第{recommended_chapter}章',
        'target_chapter': recommended_chapter,
        'can_start': can_start
    }
