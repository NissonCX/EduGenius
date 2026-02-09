"""
缓存工具模块

提供缓存装饰器和辅助函数，简化 API 端点的缓存使用
"""
import json
import hashlib
import logging
from functools import wraps
from typing import Optional, Callable, Any, Union
from datetime import timedelta

from app.core.redis_client import get_redis, redis_client

logger = logging.getLogger(__name__)


# 缓存时间配置（秒）
CACHE_TTL = {
    'short': 60,          # 1 分钟 - 频繁变化的数据
    'medium': 300,        # 5 分钟 - 中等频率变化
    'long': 900,          # 15 分钟 - 较少变化的数据
    'very_long': 3600,    # 1 小时 - 很少变化的数据
    'daily': 86400,       # 1 天 - 静态数据
}


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    生成缓存键

    Args:
        prefix: 键前缀
        *args, **kwargs: 用于生成唯一标识的参数

    Returns:
        缓存键字符串
    """
    # 将参数序列化为字符串
    key_parts = [prefix]

    if args:
        key_parts.extend(str(arg) for arg in args)

    if kwargs:
        # 排序 kwargs 确保相同的参数生成相同的键
        sorted_kwargs = sorted(kwargs.items())
        key_parts.extend(f"{k}={v}" for k, v in sorted_kwargs)

    key_string = ":".join(key_parts)

    # 如果键太长，使用哈希
    if len(key_string) > 200:
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:8]
        return f"{prefix}:hash:{key_hash}"

    return key_string


def cache_response(
    prefix: str,
    ttl: Union[int, str] = 'medium',
    exclude_params: Optional[list] = None,
    include_params: Optional[list] = None,
    condition: Optional[Callable] = None
):
    """
    缓存异步函数返回值的装饰器

    Args:
        prefix: 缓存键前缀
        ttl: 过期时间（秒）或预设名称 ('short', 'medium', 'long', 'very_long', 'daily')
        exclude_params: 排除的参数名列表
        include_params: 包含的参数名列表（如果指定，只使用这些参数生成键）
        condition: 缓存条件函数，返回 True 才缓存

    Example:
        @cache_response('user_info', ttl='long')
        async def get_user_info(user_id: int):
            return await db.query(User).filter(User.id == user_id).first()
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 检查缓存条件
            if condition and not condition():
                return await func(*args, **kwargs)

            # 生成缓存键
            cache_kwargs = kwargs.copy()

            # 过滤参数
            if exclude_params:
                cache_kwargs = {k: v for k, v in cache_kwargs.items() if k not in exclude_params}
            if include_params:
                cache_kwargs = {k: v for k, v in cache_kwargs.items() if k in include_params}

            cache_key = generate_cache_key(prefix, *args, **cache_kwargs)

            # 尝试从缓存获取
            client = await get_redis()
            if client:
                try:
                    cached_value = await client.get_json(cache_key)
                    if cached_value is not None:
                        logger.debug(f"✅ 缓存命中: {cache_key}")
                        return cached_value
                except Exception as e:
                    logger.warning(f"缓存读取失败: {e}")

            # 缓存未命中，执行函数
            logger.debug(f"❌ 缓存未命中: {cache_key}")
            result = await func(*args, **kwargs)

            # 存入缓存
            if client and result is not None:
                try:
                    # 解析 TTL
                    if isinstance(ttl, str):
                        expire_seconds = CACHE_TTL.get(ttl, CACHE_TTL['medium'])
                    else:
                        expire_seconds = ttl

                    await client.set_json(cache_key, result, expire=expire_seconds)
                    logger.debug(f"💾 已缓存: {cache_key} (TTL: {expire_seconds}s)")
                except Exception as e:
                    logger.warning(f"缓存写入失败: {e}")

            return result

        return wrapper
    return decorator


def cache_invalidate(
    prefix: str,
    args: Optional[tuple] = None,
    kwargs: Optional[dict] = None
):
    """
    使缓存失效的装饰器（用于写操作后自动清理相关缓存）

    Args:
        prefix: 要清理的缓存键前缀
        args: 用于生成特定缓存键的参数
        kwargs: 用于生成特定缓存键的参数

    Example:
        @cache_invalidate('user_info')
        async def update_user(user_id: int, **data):
            return await db.query(User).filter(User.id == user_id).update(**data)
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args_func, **kwargs_func):
            # 执行原函数
            result = await func(*args_func, **kwargs_func)

            # 清理缓存
            client = await get_redis()
            if client:
                try:
                    # 如果指定了参数，删除特定键
                    if args is not None or kwargs is not None:
                        cache_key = generate_cache_key(prefix, *(args or ()), **(kwargs or {}))
                        await client.delete(cache_key)
                        logger.debug(f"🗑️ 已清理缓存: {cache_key}")
                    else:
                        # 删除所有匹配前缀的键
                        count = await client.delete_pattern(f"{prefix}:*")
                        logger.debug(f"🗑️ 已清理 {count} 个缓存键: {prefix}:*")
                except Exception as e:
                    logger.warning(f"缓存清理失败: {e}")

            return result

        return wrapper
    return decorator


async def cache_get(prefix: str, *args, **kwargs) -> Optional[Any]:
    """
    手动获取缓存值

    Args:
        prefix: 缓存键前缀
        *args, **kwargs: 用于生成缓存键的参数

    Returns:
        缓存的值，不存在返回 None
    """
    client = await get_redis()
    if not client:
        return None

    cache_key = generate_cache_key(prefix, *args, **kwargs)
    return await client.get_json(cache_key)


async def cache_set(
    prefix: str,
    value: Any,
    ttl: Union[int, str] = 'medium',
    *args,
    **kwargs
) -> bool:
    """
    手动设置缓存值

    Args:
        prefix: 缓存键前缀
        value: 要缓存的值
        ttl: 过期时间
        *args, **kwargs: 用于生成缓存键的参数

    Returns:
        是否成功
    """
    client = await get_redis()
    if not client:
        return False

    cache_key = generate_cache_key(prefix, *args, **kwargs)

    # 解析 TTL
    if isinstance(ttl, str):
        expire_seconds = CACHE_TTL.get(ttl, CACHE_TTL['medium'])
    else:
        expire_seconds = ttl

    return await client.set_json(cache_key, value, expire=expire_seconds)


async def cache_delete(prefix: str, *args, **kwargs) -> bool:
    """
    手动删除缓存值

    Args:
        prefix: 缓存键前缀
        *args, **kwargs: 用于生成缓存键的参数

    Returns:
        是否成功
    """
    client = await get_redis()
    if not client:
        return False

    cache_key = generate_cache_key(prefix, *args, **kwargs)
    return await client.delete(cache_key)


async def cache_delete_pattern(prefix: str) -> int:
    """
    批量删除匹配前缀的所有缓存

    Args:
        prefix: 缓存键前缀

    Returns:
        删除的键数量
    """
    client = await get_redis()
    if not client:
        return 0

    return await client.delete_pattern(f"{prefix}:*")


class CacheKeyBuilder:
    """缓存键构建器 - 提供结构化的缓存键生成"""

    # 用户相关
    USER_INFO = "user:info"
    USER_PROGRESS = "user:progress"
    USER_HISTORY = "user:history"

    # 文档相关
    DOC_INFO = "doc:info"
    DOC_CHAPTERS = "doc:chapters"
    DOC_CONTENT = "doc:content"

    # 章节相关
    CHAPTER_INFO = "chapter:info"
    CHAPTER_CONTENT = "chapter:content"
    CHAPTER_PROGRESS = "chapter:progress"

    # 测验相关
    QUIZ_QUESTIONS = "quiz:questions"
    QUIZ_RESULTS = "quiz:results"

    # 系统相关
    HEALTH_CHECK = "system:health"
    STATS = "system:stats"

    @classmethod
    def user(cls, user_id: int) -> dict:
        """用户相关的缓存键"""
        return {
            'info': f"{cls.USER_INFO}:{user_id}",
            'progress': f"{cls.USER_PROGRESS}:{user_id}",
            'history': f"{cls.USER_HISTORY}:{user_id}",
        }

    @classmethod
    def document(cls, doc_id: int) -> dict:
        """文档相关的缓存键"""
        return {
            'info': f"{cls.DOC_INFO}:{doc_id}",
            'chapters': f"{cls.DOC_CHAPTERS}:{doc_id}",
        }

    @classmethod
    def chapter(cls, doc_id: int, chapter_num: int) -> dict:
        """章节相关的缓存键"""
        return {
            'info': f"{cls.CHAPTER_INFO}:{doc_id}:{chapter_num}",
            'content': f"{cls.CHAPTER_CONTENT}:{doc_id}:{chapter_num}",
        }


# 预定义的缓存装饰器
cache_user_info = cache_response(
    CacheKeyBuilder.USER_INFO,
    ttl='long',
    include_params=['user_id']
)

cache_document_info = cache_response(
    CacheKeyBuilder.DOC_INFO,
    ttl='very_long',
    include_params=['document_id']
)

cache_chapters = cache_response(
    CacheKeyBuilder.DOC_CHAPTERS,
    ttl='very_long',
    include_params=['document_id']
)

cache_chapter_content = cache_response(
    CacheKeyBuilder.CHAPTER_CONTENT,
    ttl='long',
    include_params=['document_id', 'chapter_number']
)
