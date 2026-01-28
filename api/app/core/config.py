"""
EduGenius Configuration Management
统一管理所有配置和环境变量
"""
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

class Settings:
    """应用配置类"""

    # API 密钥
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")  # 备用

    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./edugenius.db")

    # ChromaDB 配置
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

    # 应用配置
    APP_NAME: str = "EduGenius"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # CORS 配置
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ]

    # AI 模型配置
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "qwen-max")
    FALLBACK_MODEL: str = os.getenv("FALLBACK_MODEL", "qwen-plus")

    # 教学配置
    MAX_QUESTIONS_PER_SESSION: int = int(os.getenv("MAX_QUESTIONS_PER_SESSION", "5"))
    DEFAULT_STUDENT_LEVEL: int = int(os.getenv("DEFAULT_STUDENT_LEVEL", "3"))

    # 文档处理配置
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))

    def validate(self) -> bool:
        """验证配置是否有效"""
        if not self.DASHSCOPE_API_KEY:
            print("⚠️  警告: DASHSCOPE_API_KEY 未设置")
            return False
        return True

    class Config:
        case_sensitive = True


# 全局配置实例
settings = Settings()

# 导出便捷访问
DASHSCOPE_API_KEY = settings.DASHSCOPE_API_KEY
DATABASE_URL = settings.DATABASE_URL
CHROMA_PERSIST_DIR = settings.CHROMA_PERSIST_DIR
DEFAULT_MODEL = settings.DEFAULT_MODEL


def get_model_name(level: int = 3) -> str:
    """
    根据学生等级选择合适的模型

    Args:
        level: 学生认知等级 (1-5)

    Returns:
        模型名称
    """
    # 等级 1-2 使用较快的模型（降低成本）
    if level <= 2:
        return os.getenv("FAST_MODEL", "qwen-plus")

    # 等级 3-5 使用最强模型
    return settings.DEFAULT_MODEL


if __name__ == "__main__":
    # 测试配置加载
    print(f"📋 {settings.APP_NAME} v{settings.APP_VERSION} 配置检查")
    print(f"✅ DashScope API Key: {'已设置' * bool(settings.DASHSCOPE_API_KEY)}")
    print(f"📊 数据库: {settings.DATABASE_URL}")
    print(f"🧠 默认模型: {settings.DEFAULT_MODEL}")
    print(f"🎯 学生等级: {settings.DEFAULT_STUDENT_LEVEL}")
