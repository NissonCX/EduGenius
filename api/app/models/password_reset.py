"""
密码重置模型

存储密码重置令牌和过期时间
"""
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class PasswordReset(Base):
    """密码重置令牌模型"""
    __tablename__ = "password_resets"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), index=True, nullable=False)
    token = Column(String(255), unique=True, index=True, nullable=False)

    # 令牌过期时间（默认1小时）
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # 是否已使用
    used = Column(Integer, default=0)  # 0 = 未使用, 1 = 已使用

    # 创建时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<PasswordReset(id={self.id}, email='{self.email}', used={self.used})>"
