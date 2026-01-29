"""
结构化日志配置
"""
import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """JSON 格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加额外字段
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """彩色控制台格式化器"""
    
    # ANSI 颜色码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        # 添加颜色
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        
        # 格式化消息
        formatted = super().format(record)
        
        # 重置 levelname（避免影响其他 handler）
        record.levelname = levelname
        
        return formatted


def setup_logging(
    log_level: str = "INFO",
    log_file: str = "/tmp/edugenius_backend.log",
    enable_json: bool = False
) -> logging.Logger:
    """
    配置日志系统
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径
        enable_json: 是否启用 JSON 格式（生产环境推荐）
    
    Returns:
        logging.Logger: 配置好的 logger
    """
    # 创建日志目录
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 获取根 logger
    logger = logging.getLogger("edugenius")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除现有 handlers
    logger.handlers.clear()
    
    # 控制台 Handler（彩色输出）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    if enable_json:
        console_formatter = JSONFormatter()
    else:
        console_formatter = ColoredFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 文件 Handler（JSON 格式）
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_formatter = JSONFormatter()
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # 错误日志单独文件
    error_log_file = log_path.parent / f"{log_path.stem}_error.log"
    error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    logger.addHandler(error_handler)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    获取 logger 实例
    
    Args:
        name: logger 名称，默认为调用模块名
    
    Returns:
        logging.Logger: logger 实例
    """
    if name:
        return logging.getLogger(f"edugenius.{name}")
    return logging.getLogger("edugenius")


# ============ 日志辅助函数 ============
def log_api_request(
    logger: logging.Logger,
    method: str,
    path: str,
    user_id: int = None,
    **kwargs
):
    """记录 API 请求"""
    logger.info(
        f"API Request: {method} {path}",
        extra={
            "event_type": "api_request",
            "method": method,
            "path": path,
            "user_id": user_id,
            **kwargs
        }
    )


def log_api_response(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: int = None,
    **kwargs
):
    """记录 API 响应"""
    logger.info(
        f"API Response: {method} {path} - {status_code} ({duration_ms:.2f}ms)",
        extra={
            "event_type": "api_response",
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "user_id": user_id,
            **kwargs
        }
    )


def log_database_query(
    logger: logging.Logger,
    query_type: str,
    table: str,
    duration_ms: float,
    **kwargs
):
    """记录数据库查询"""
    logger.debug(
        f"DB Query: {query_type} on {table} ({duration_ms:.2f}ms)",
        extra={
            "event_type": "database_query",
            "query_type": query_type,
            "table": table,
            "duration_ms": duration_ms,
            **kwargs
        }
    )


def log_ai_request(
    logger: logging.Logger,
    model: str,
    prompt_length: int,
    response_length: int = None,
    duration_ms: float = None,
    **kwargs
):
    """记录 AI 请求"""
    logger.info(
        f"AI Request: {model} (prompt: {prompt_length} chars)",
        extra={
            "event_type": "ai_request",
            "model": model,
            "prompt_length": prompt_length,
            "response_length": response_length,
            "duration_ms": duration_ms,
            **kwargs
        }
    )


def log_document_processing(
    logger: logging.Logger,
    document_id: int,
    filename: str,
    status: str,
    duration_ms: float = None,
    **kwargs
):
    """记录文档处理"""
    logger.info(
        f"Document Processing: {filename} - {status}",
        extra={
            "event_type": "document_processing",
            "document_id": document_id,
            "filename": filename,
            "status": status,
            "duration_ms": duration_ms,
            **kwargs
        }
    )


def log_user_action(
    logger: logging.Logger,
    user_id: int,
    action: str,
    **kwargs
):
    """记录用户行为"""
    logger.info(
        f"User Action: {action} (user_id: {user_id})",
        extra={
            "event_type": "user_action",
            "user_id": user_id,
            "action": action,
            **kwargs
        }
    )


# ============ 性能监控装饰器 ============
import time
from functools import wraps


def log_performance(logger: logging.Logger = None):
    """性能监控装饰器"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            _logger = logger or get_logger(func.__module__)
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                _logger.debug(
                    f"Function {func.__name__} completed in {duration_ms:.2f}ms",
                    extra={
                        "event_type": "performance",
                        "function": func.__name__,
                        "duration_ms": duration_ms,
                        "success": True
                    }
                )
                
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                _logger.error(
                    f"Function {func.__name__} failed after {duration_ms:.2f}ms: {str(e)}",
                    extra={
                        "event_type": "performance",
                        "function": func.__name__,
                        "duration_ms": duration_ms,
                        "success": False,
                        "error": str(e)
                    }
                )
                
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            _logger = logger or get_logger(func.__module__)
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                _logger.debug(
                    f"Function {func.__name__} completed in {duration_ms:.2f}ms",
                    extra={
                        "event_type": "performance",
                        "function": func.__name__,
                        "duration_ms": duration_ms,
                        "success": True
                    }
                )
                
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                _logger.error(
                    f"Function {func.__name__} failed after {duration_ms:.2f}ms: {str(e)}",
                    extra={
                        "event_type": "performance",
                        "function": func.__name__,
                        "duration_ms": duration_ms,
                        "success": False,
                        "error": str(e)
                    }
                )
                
                raise
        
        # 判断是否为异步函数
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
