"""
Database models for EduGenius platform.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class User(Base):
    """User model with preferred teaching style (1-5)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)  # 哈希密码

    # 导师风格偏好: 1=温柔, 2=耐心, 3=标准, 4=严格, 5=严厉
    # 字段名保持 cognitive_level 以兼容现有数据库，但语义改为教学风格偏好
    cognitive_level = Column(Integer, default=3, nullable=False)

    # Learning progress metrics
    total_documents_studied = Column(Integer, default=0)
    total_chapters_completed = Column(Integer, default=0)
    overall_progress_percentage = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', style=L{self.cognitive_level})>"


class Document(Base):
    """Document model with MD5-based deduplication."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    # MD5 hash for deduplication (unique identifier)
    md5_hash = Column(String(32), unique=True, index=True, nullable=False)

    # Document metadata
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # 'pdf', 'txt', 'docx'
    file_size = Column(Integer)  # Size in bytes

    # Content summary
    title = Column(String(500))
    total_pages = Column(Integer, default=0)
    total_chapters = Column(Integer, default=0)

    # Processing status
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    chroma_collection_name = Column(String(100))  # ChromaDB collection name (MD5-based)

    # OCR-related fields
    has_text_layer = Column(Integer, default=1)  # 1 = has text layer, 0 = scanned/OCR
    ocr_confidence = Column(Float, default=0.0)  # OCR confidence score (0-1)
    current_page = Column(Integer, default=0)  # Current processing page (for OCR progress)

    # Owner
    uploaded_by = Column(Integer, ForeignKey("users.id"))

    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<Document(id={self.id}, md5='{self.md5_hash}', filename='{self.filename}')>"


class Progress(Base):
    """Progress tracking for user-document-chapter combinations."""
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True, index=True)

    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)

    # Chapter/Section tracking
    chapter_number = Column(Integer, nullable=False)
    chapter_title = Column(String(500))

    # Progress status
    status = Column(String(50), default="not_started")  # not_started, in_progress, completed, locked
    completion_percentage = Column(Float, default=0.0)

    # Adaptive learning data
    cognitive_level_assigned = Column(Integer)  # L1-L5 level when assigned
    time_spent_minutes = Column(Integer, default=0)
    quiz_attempts = Column(Integer, default=0)
    quiz_success_rate = Column(Float, default=0.0)

    # Timestamps
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    last_accessed_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Progress(id={self.id}, user_id={self.user_id}, chapter={self.chapter_number}, status={self.status})>"


class ConversationHistory(Base):
    """对话历史记录"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"))
    chapter_number = Column(Integer)

    # 对话内容
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)

    # 附加数据
    student_level_at_time = Column(Integer)  # 对话时的学生等级
    extra_metadata = Column(Text)  # JSON 格式的额外信息（重命名以避免与 SQLAlchemy 保留字冲突）

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Conversation(id={self.id}, role={self.role}, user_id={self.user_id})>"


class QuizAttempt(Base):
    """题目尝试记录"""
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    progress_id = Column(Integer, ForeignKey("progress.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)

    # 题目信息
    question_text = Column(Text, nullable=False)
    user_answer = Column(String(500))
    correct_answer = Column(String(500))
    is_correct = Column(Integer, nullable=False)  # 0 or 1

    # 元数据
    time_spent_seconds = Column(Integer)
    attempts_count = Column(Integer, default=1)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<QuizAttempt(id={self.id}, correct={self.is_correct})>"


class Question(Base):
    """题目数据库模型"""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)

    # 关联文档和章节
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chapter_number = Column(Integer, nullable=False)

    # 题目基本信息
    question_type = Column(String(50), nullable=False)  # 'choice', 'fill_blank', 'essay'
    question_text = Column(Text, nullable=False)

    # 选项（JSON格式，用于选择题）
    # 格式: {"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}
    options = Column(Text)

    # 答案和解析
    correct_answer = Column(String(500), nullable=False)
    explanation = Column(Text)  # 题目解析

    # 难度和分类
    difficulty = Column(Integer, default=3)  # 1-5难度
    competency_dimension = Column(String(50))  # 能力维度: comprehension, logic, terminology, memory, application, stability

    # 元数据
    created_by = Column(String(50), default="AI")  # AI生成或人工创建
    is_active = Column(Integer, default=1)  # 是否启用

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Question(id={self.id}, type={self.question_type}, chapter={self.chapter_number})>"
