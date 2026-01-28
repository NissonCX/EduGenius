"""
Security utilities for password hashing and JWT token management.
"""
from datetime import datetime, timedelta
from typing import Optional
import hashlib

from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings


# ============ 密码哈希配置 ============
# 使用 argon2 替代 bcrypt（更安全且无长度限制）
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


# ============ JWT 配置 ============
SECRET_KEY = settings.DASHSCOPE_API_KEY  # 使用相同的 API 密钥作为签名密钥
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 天


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
