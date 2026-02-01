"""
Security utilities for password hashing and JWT token management.
"""
from datetime import datetime, timedelta
from typing import Optional
import hashlib

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings
from app.db.database import get_db
from app.models.document import User


# ============ 密码哈希配置 ============
# 使用 argon2 替代 bcrypt（更安全且无长度限制）
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


# ============ JWT 配置 ============
# 使用独立的 JWT Secret，如果未设置则使用默认密钥（生产环境必须设置）
SECRET_KEY = settings.JWT_SECRET_KEY or "your-super-secret-jwt-key-change-in-production-min-32-chars!"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES  # 从配置读取，默认 2 小时


class Token(BaseModel):
    """JWT Token 响应"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token 数据"""
    email: Optional[str] = None
    user_id: Optional[int] = None


# ============ 辅助函数 ============
def _sha256_hash(password: str) -> str:
    """
    使用 SHA256 预处理密码（避免 bcrypt 长度限制）

    Args:
        password: 明文密码

    Returns:
        str: SHA256 哈希后的十六进制字符串
    """
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


# ============ 密码哈希函数 ============
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码

    Returns:
        bool: 密码是否匹配
    """
    # 先 SHA256 哈希，再用 bcrypt 验证
    password_hash = _sha256_hash(plain_password)
    return pwd_context.verify(password_hash, hashed_password)


def get_password_hash(password: str) -> str:
    """
    生成密码哈希

    Args:
        password: 明文密码

    Returns:
        str: 哈希后的密码
    """
    # 先 SHA256 哈希，再用 bcrypt 哈希
    password_hash = _sha256_hash(password)
    return pwd_context.hash(password_hash)


# ============ JWT Token 函数 ============
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT Token

    Args:
        data: 要编码的数据（通常包含 user_id 和 email）
        expires_delta: 过期时间增量

    Returns:
        str: JWT Token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """
    验证 JWT Token

    Args:
        token: JWT Token 字符串

    Returns:
        TokenData: 解码后的 token 数据，如果验证失败则返回 None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")

        if email is None:
            return None

        return TokenData(email=email, user_id=user_id)

    except JWTError:
        return None


# ============ 辅助函数 ============
def create_token_for_user(user_id: int, email: str) -> str:
    """
    为用户创建 Token

    Args:
        user_id: 用户 ID
        email: 用户邮箱

    Returns:
        str: JWT Token
    """
    data = {
        "sub": email,
        "user_id": user_id,
        "type": "access"
    }
    return create_access_token(data)


# ============ FastAPI 依赖函数 ============
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    获取当前登录用户（FastAPI 依赖）

    Args:
        credentials: HTTP Bearer credentials
        db: 数据库 session

    Returns:
        User: 当前用户对象

    Raises:
        HTTPException: 如果未认证或 token 无效
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 如果没有提供 token
    if credentials is None:
        raise credentials_exception

    token = credentials.credentials

    # 验证 token
    token_data = verify_token(token)
    if token_data is None:
        raise credentials_exception

    # 从数据库获取用户
    result = await db.execute(
        select(User).where(User.id == token_data.user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    获取当前登录用户（可选，不抛出异常）

    与 get_current_user 不同，如果未认证则返回 None 而不是抛出异常

    Args:
        request: FastAPI Request 对象
        db: 数据库 session

    Returns:
        User: 当前用户对象，如果未认证则返回 None
    """
    # 从 Authorization header 获取 token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ")[1]
    token_data = verify_token(token)

    if token_data is None:
        return None

    result = await db.execute(
        select(User).where(User.id == token_data.user_id)
    )
    user = result.scalar_one_or_none()

    return user


def require_auth(user: User = Depends(get_current_user)) -> User:
    """
    强制要求认证的快捷依赖

    Args:
        user: 从 get_current_user 获取的用户

    Returns:
        User: 用户对象

    Raises:
        HTTPException: 如果用户未认证
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要登录才能访问此资源"
        )
    return user

