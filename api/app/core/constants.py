"""
应用常量定义
消除魔法数字，提高代码可维护性
"""

# ============ 用户等级相关 ============
LEVEL_THRESHOLDS = {
    5: 90,  # 专家级别
    4: 75,  # 高级
    3: 60,  # 进阶
    2: 40,  # 入门
    1: 0    # 基础
}

LEVEL_NAMES = {
    5: "专家 (Expert)",
    4: "高级 (Advanced)",
    3: "进阶 (Intermediate)",
    2: "入门 (Beginner)",
    1: "基础 (Foundation)"
}

# ============ 进度相关 ============
COMPLETION_THRESHOLD = 95  # 完成度阈值（百分比）
MIN_LEARNING_TIME_MINUTES = 10  # 最少学习时间（分钟）

# ============ 章节解锁相关 ============
UNLOCK_CONFIG = {
    "completion_threshold": 0.70,  # 70% 完成度
    "quiz_score_threshold": 0.60,  # 60% 测试分数
    "min_time_minutes": 10  # 最少10分钟学习时间
}

# ============ 文件上传相关 ============
MAX_FILE_SIZE_MB = 50  # 最大文件大小（MB）
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_FILE_TYPES = ["pdf", "txt"]

# ============ Session 相关 ============
SESSION_TTL_SECONDS = 3600  # 1小时过期
MAX_SESSIONS = 1000  # 最大 session 数量
SESSION_CLEANUP_INTERVAL_SECONDS = 300  # 5分钟清理一次

# ============ SSE 超时相关 ============
SSE_TIMEOUT_TEACHING_SESSION = 300  # 5分钟
SSE_TIMEOUT_TUTOR_RESPONSE = 120    # 2分钟
SSE_TIMEOUT_CHAT = 180              # 3分钟

# ============ 能力评估相关 ============
COMPETENCY_DIMENSIONS = [
    'comprehension',  # 理解能力
    'logic',          # 逻辑能力
    'terminology',    # 术语掌握
    'memory',         # 记忆能力
    'application',    # 应用能力
    'stability'       # 稳定性
]

DEFAULT_COMPETENCY_SCORE = 50  # 默认能力分数

# 答题时间评分标准（秒）
IDEAL_ANSWER_TIME_MIN = 30
IDEAL_ANSWER_TIME_MAX = 120
TIME_BONUS_POINTS = 5
TIME_PENALTY_POINTS = -5

# ============ 章节划分相关 ============
TOC_EXTRACT_LENGTH = 10000  # 提取目录的字符数
TOC_KEYWORDS = ['目录', '目　录', 'Contents', 'TABLE OF CONTENTS', '章节目录']

# ============ 数据库相关 ============
DEFAULT_COGNITIVE_LEVEL = 3  # 默认认知等级
DEFAULT_TEACHING_STYLE = 3   # 默认教学风格

# ============ Token 相关 ============
TOKEN_EXPIRE_HOURS = 2  # Token 过期时间（小时）
REFRESH_TOKEN_EXPIRE_DAYS = 7  # Refresh Token 过期时间（天）

# ============ 密码相关 ============
MIN_PASSWORD_LENGTH = 8  # 最小密码长度
PASSWORD_REQUIREMENTS = {
    "min_length": 8,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_digit": True,
    "require_special": False  # 可选：特殊字符
}

# ============ 分页相关 ============
DEFAULT_PAGE_SIZE = 20  # 默认每页数量
MAX_PAGE_SIZE = 100     # 最大每页数量

# ============ 缓存相关 ============
CACHE_TTL_SECONDS = 60  # 缓存过期时间（秒）

# ============ 日志相关 ============
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
DEFAULT_LOG_LEVEL = "INFO"
