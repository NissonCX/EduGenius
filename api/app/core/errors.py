"""
统一错误处理和错误码系统
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError
import logging
from typing import Union

logger = logging.getLogger(__name__)


# ============ 错误码定义 ============
class ErrorCode:
    """统一错误码"""
    # 通用错误 (1000-1999)
    UNKNOWN_ERROR = 1000
    VALIDATION_ERROR = 1001
    DATABASE_ERROR = 1002
    NOT_FOUND = 1003
    PERMISSION_DENIED = 1004
    
    # 认证错误 (2000-2999)
    INVALID_CREDENTIALS = 2000
    TOKEN_EXPIRED = 2001
    TOKEN_INVALID = 2002
    UNAUTHORIZED = 2003
    
    # 用户错误 (3000-3999)
    USER_NOT_FOUND = 3000
    USER_ALREADY_EXISTS = 3001
    WEAK_PASSWORD = 3002
    INVALID_USERNAME = 3003
    
    # 文档错误 (4000-4999)
    DOCUMENT_NOT_FOUND = 4000
    DOCUMENT_UPLOAD_FAILED = 4001
    FILE_TOO_LARGE = 4002
    UNSUPPORTED_FILE_TYPE = 4003
    DOCUMENT_PROCESSING_FAILED = 4004
    
    # 章节错误 (5000-5999)
    CHAPTER_NOT_FOUND = 5000
    CHAPTER_LOCKED = 5001
    INVALID_CHAPTER_NUMBER = 5002
    
    # 测验错误 (6000-6999)
    QUESTION_NOT_FOUND = 6000
    INVALID_ANSWER = 6001
    TEST_NOT_FOUND = 6002
    INSUFFICIENT_QUESTIONS = 6003


# ============ 自定义异常类 ============
class AppException(Exception):
    """应用基础异常"""
    def __init__(
        self,
        message: str,
        error_code: int = ErrorCode.UNKNOWN_ERROR,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(AppException):
    """验证异常"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class NotFoundException(AppException):
    """资源未找到异常"""
    def __init__(self, message: str, error_code: int = ErrorCode.NOT_FOUND):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_404_NOT_FOUND
        )


class AuthenticationException(AppException):
    """认证异常"""
    def __init__(self, message: str, error_code: int = ErrorCode.UNAUTHORIZED):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class PermissionException(AppException):
    """权限异常"""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code=ErrorCode.PERMISSION_DENIED,
            status_code=status.HTTP_403_FORBIDDEN
        )


# ============ 错误响应格式化 ============
def format_error_response(
    error_code: int,
    message: str,
    details: dict = None,
    path: str = None
) -> dict:
    """格式化错误响应"""
    response = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
        }
    }
    
    if details:
        response["error"]["details"] = details
    
    if path:
        response["error"]["path"] = path
    
    return response


# ============ 异常处理器 ============
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """处理应用自定义异常"""
    logger.error(
        f"AppException: {exc.message}",
        extra={
            "error_code": exc.error_code,
            "path": request.url.path,
            "details": exc.details
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            path=request.url.path
        )
    )


async def validation_exception_handler(
    request: Request,
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """处理 Pydantic 验证异常"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(
        f"Validation error: {request.url.path}",
        extra={"errors": errors}
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=format_error_response(
            error_code=ErrorCode.VALIDATION_ERROR,
            message="请求参数验证失败",
            details={"errors": errors},
            path=request.url.path
        )
    )


async def sqlalchemy_exception_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """处理数据库异常"""
    logger.error(
        f"Database error: {str(exc)}",
        extra={"path": request.url.path},
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=format_error_response(
            error_code=ErrorCode.DATABASE_ERROR,
            message="数据库操作失败，请稍后重试",
            path=request.url.path
        )
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """处理未捕获的异常"""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={"path": request.url.path},
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=format_error_response(
            error_code=ErrorCode.UNKNOWN_ERROR,
            message="服务器内部错误，请稍后重试",
            path=request.url.path
        )
    )


# ============ 注册异常处理器 ============
def register_exception_handlers(app):
    """注册所有异常处理器到 FastAPI 应用"""
    from fastapi.exceptions import RequestValidationError
    from pydantic import ValidationError
    from sqlalchemy.exc import SQLAlchemyError
    
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
