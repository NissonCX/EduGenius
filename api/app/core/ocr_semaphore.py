"""
OCR 并发控制模块
防止多个用户同时上传扫描版PDF导致服务器内存溢出
"""
import asyncio
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class OCRSemaphore:
    """OCR 处理信号量 - 防止内存溢出"""

    def __init__(self, max_concurrent: int = 2):
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._max_concurrent = max_concurrent
        self._current_tasks = set()

    async def acquire(self, task_id: str) -> bool:
        """尝试获取处理槽位"""
        try:
            await self._semaphore.acquire()
            self._current_tasks.add(task_id)
            logger.info(f"🔓 OCR 任务 {task_id} 获得处理槽位 (当前活跃: {len(self._current_tasks)}/{self._max_concurrent})")
            return True
        except Exception as e:
            logger.error(f"❌ OCR 任务 {task_id} 获取槽位失败: {e}")
            return False

    def release(self, task_id: str):
        """释放处理槽位"""
        if task_id in self._current_tasks:
            self._current_tasks.remove(task_id)
            self._semaphore.release()
            logger.info(f"🔓 OCR 任务 {task_id} 释放槽位 (当前活跃: {len(self._current_tasks)}/{self._max_concurrent})")

    def get_status(self) -> dict:
        """获取当前状态"""
        return {
            "max_concurrent": self._max_concurrent,
            "current_tasks": len(self._current_tasks),
            "available_slots": self._max_concurrent - len(self._current_tasks),
            "active_tasks": list(self._current_tasks)
        }


# 全局 OCR 信号量实例（限制最多2个并发OCR任务）
ocr_semaphore = OCRSemaphore(max_concurrent=2)
