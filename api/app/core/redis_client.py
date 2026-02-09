"""
Redis 客户端管理模块

提供 Redis 连接管理和基本操作封装
"""
import json
import logging
from typing import Optional, Any, List
from datetime import timedelta

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Redis 异步客户端封装

    提供常用的缓存操作，支持字符串、JSON 序列化
    """

    def __init__(self):
        """初始化 Redis 客户端"""
        if not REDIS_AVAILABLE:
            logger.warning("⚠️ Redis 模块未安装，缓存功能将被禁用")
            self._client = None
            return

        self._client: Optional[aioredis.Redis] = None
        self._connected = False

    async def connect(self, url: str = None, **kwargs) -> bool:
        """
        连接到 Redis 服务器

        Args:
            url: Redis 连接 URL (默认从配置读取)
            **kwargs: 额外的连接参数

        Returns:
            bool: 连接是否成功
        """
        if not REDIS_AVAILABLE:
            logger.warning("Redis 模块未安装，跳过连接")
            return False

        if self._connected:
            return True

        try:
            # 默认连接配置
            if url is None:
                redis_host = kwargs.get('host', getattr(settings, 'REDIS_HOST', 'localhost'))
                redis_port = kwargs.get('port', getattr(settings, 'REDIS_PORT', 6379))
                redis_db = kwargs.get('db', getattr(settings, 'REDIS_DB', 0))
                redis_password = kwargs.get('password', getattr(settings, 'REDIS_PASSWORD', None))
                url = f"redis://{':'.join(['****', redis_password]) if redis_password else 'redis'}@{redis_host}:{redis_port}/{redis_db}"

            self._client = await aioredis.from_url(
                url or f"redis://{getattr(settings, 'REDIS_HOST', 'localhost')}:{getattr(settings, 'REDIS_PORT', 6379)}/{getattr(settings, 'REDIS_DB', 0)}",
                password=kwargs.get('password', getattr(settings, 'REDIS_PASSWORD', None)),
                encoding="utf-8",
                decode_responses=True,
                **kwargs
            )

            # 测试连接
            await self._client.ping()
            self._connected = True
            logger.info(f"✅ Redis 连接成功: {url}")
            return True

        except Exception as e:
            logger.error(f"❌ Redis 连接失败: {e}")
            self._client = None
            self._connected = False
            return False

    async def disconnect(self):
        """关闭 Redis 连接"""
        if self._client:
            await self._client.close()
            self._connected = False
            logger.info("🔌 Redis 连接已关闭")

    async def is_connected(self) -> bool:
        """检查是否已连接"""
        if not self._connected or not self._client:
            return False
        try:
            await self._client.ping()
            return True
        except:
            return False

    async def get(self, key: str) -> Optional[str]:
        """获取字符串值"""
        if not self._connected:
            return None
        try:
            return await self._client.get(key)
        except Exception as e:
            logger.error(f"Redis GET 失败: {e}")
            return None

    async def set(
        self,
        key: str,
        value: str,
        expire: Optional[int] = None
    ) -> bool:
        """
        设置字符串值

        Args:
            key: 键
            value: 值
            expire: 过期时间（秒）

        Returns:
            bool: 是否成功
        """
        if not self._connected:
            return False
        try:
            await self._client.set(key, value, ex=expire)
            return True
        except Exception as e:
            logger.error(f"Redis SET 失败: {e}")
            return False

    async def get_json(self, key: str) -> Optional[Any]:
        """
        获取 JSON 对象

        Args:
            key: 键

        Returns:
            解析后的 JSON 对象，失败返回 None
        """
        value = await self.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            logger.error(f"JSON 解析失败: {key}")
            return None

    async def set_json(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """
        设置 JSON 对象

        Args:
            key: 键
            value: 任意可序列化的 Python 对象
            expire: 过期时间（秒）

        Returns:
            bool: 是否成功
        """
        try:
            json_value = json.dumps(value, ensure_ascii=False)
            return await self.set(key, json_value, expire)
        except Exception as e:
            logger.error(f"JSON 序列化失败: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """删除键"""
        if not self._connected:
            return False
        try:
            await self._client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE 失败: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        批量删除匹配的键

        Args:
            pattern: 匹配模式 (例如: "user:*")

        Returns:
            删除的键数量
        """
        if not self._connected:
            return 0
        try:
            keys = await self._client.keys(pattern)
            if keys:
                return await self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis DELETE_PATTERN 失败: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self._connected:
            return False
        try:
            return await self._client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS 失败: {e}")
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """设置键的过期时间"""
        if not self._connected:
            return False
        try:
            return await self._client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Redis EXPIRE 失败: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """
        获取键的剩余生存时间

        Returns:
            秒数，-1 表示没有过期时间，-2 表示键不存在
        """
        if not self._connected:
            return -2
        try:
            return await self._client.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL 失败: {e}")
            return -2

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """原子递增"""
        if not self._connected:
            return None
        try:
            return await self._client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis INCR 失败: {e}")
            return None

    async def keys(self, pattern: str = "*") -> List[str]:
        """获取匹配的所有键"""
        if not self._connected:
            return []
        try:
            return await self._client.keys(pattern)
        except Exception as e:
            logger.error(f"Redis KEYS 失败: {e}")
            return []

    async def flush_db(self) -> bool:
        """清空当前数据库"""
        if not self._connected:
            return False
        try:
            await self._client.flushdb()
            logger.warning("⚠️ Redis 数据库已清空")
            return True
        except Exception as e:
            logger.error(f"Redis FLUSHDB 失败: {e}")
            return False


# 全局 Redis 客户端实例
redis_client: Optional[RedisClient] = None


async def get_redis() -> Optional[RedisClient]:
    """
    获取全局 Redis 客户端

    Returns:
        RedisClient 实例，如果未初始化则返回 None
    """
    global redis_client
    if redis_client is None:
        redis_client = RedisClient()
        # 自动连接
        await redis_client.connect()
    return redis_client if await redis_client.is_connected() else None


async def init_redis():
    """
    初始化 Redis 连接（在应用启动时调用）
    """
    global redis_client
    if redis_client is None:
        redis_client = RedisClient()

    success = await redis_client.connect()
    if success:
        logger.info("🚀 Redis 缓存系统已启动")
    else:
        logger.warning("⚠️ Redis 缓存系统未启用，将继续使用数据库查询")

    return success


async def close_redis():
    """
    关闭 Redis 连接（在应用关闭时调用）
    """
    global redis_client
    if redis_client:
        await redis_client.disconnect()
        redis_client = None
