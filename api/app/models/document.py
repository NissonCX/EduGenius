"""
Database models for EduGenius platform.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class User(Base):
    """User model with preferred teaching style (1-5).

    教学风格偏好（Teaching Style）:
    - 1 (温柔): 耐心细致，用简单的例子和鼓励帮助学生理解
    - 2 (耐心): 循序渐进，提供详细的讲解和指导
    - 3 (标准): 平衡严谨，既讲清原理又注重应用
    - 4 (严格): 注重细节，要求深入理解每一步推理
    - 5 (严厉): 挑战思维，培养独立解决问题的能力

    注意: 数据库字段名为 cognitive_level 以保持向后兼容，
          但实际语义为教学风格偏好。建议使用 teaching_style 属性。
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)  # 哈希密码

    # 教学风格偏好 (1-5)
    # 数据库字段名: cognitive_level (历史遗留，保持兼容性)
    cognitive_level = Column(Integer, default=3, nullable=False, index=True)

    # Refresh Token (用于获取新的 access token)
    refresh_token = Column(String(500), nullable=True)

    # Learning progress metrics
    total_documents_studied = Column(Integer, default=0)
    total_chapters_completed = Column(Integer, default=0)
    overall_progress_percentage = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index('idx_user_created', 'created_at'),
    )

    @property
    def teaching_style(self) -> int:
        """获取教学风格偏好（推荐使用此属性而非 cognitive_level）."""
        return self.cognitive_level

    @teaching_style.setter
    def teaching_style(self, value: int):
        """设置教学风格偏好."""
        if not 1 <= value <= 5:
            raise ValueError("teaching_style must be between 1 and 5")
        self.cognitive_level = value

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', style=L{self.cognitive_level})>"


class Document(Base):
    """Document model with MD5-based deduplication."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    # MD5 hash for deduplication (unique identifier)
    md5_hash = Column(String(32), unique=True, index=True, nullable=False)

    # Document metadata
    filename = Column(String(255), nullable=False, index=True)
    file_type = Column(String(50), nullable=False, index=True)  # 'pdf', 'txt', 'docx'
    file_size = Column(Integer)  # Size in bytes

    # Content summary
    title = Column(String(500))
    total_pages = Column(Integer, default=0)
    total_chapters = Column(Integer, default=0)

    # Processing status
    processing_status = Column(String(50), default="pending", index=True)  # pending, processing, completed, failed
    chroma_collection_name = Column(String(100))  # ChromaDB collection name (MD5-based)

    # OCR-related fields
    has_text_layer = Column(Integer, default=1)  # 1 = has text layer, 0 = scanned/OCR
    ocr_confidence = Column(Float, default=0.0)  # OCR confidence score (0-1)
    current_page = Column(Integer, default=0)  # Current processing page (for OCR progress)

    # Owner
    uploaded_by = Column(Integer, ForeignKey("users.id"), index=True)

    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    processed_at = Column(DateTime(timezone=True))

    __table_args__ = (
        Index('idx_document_status_uploaded', 'processing_status', 'uploaded_at'),
        Index('idx_document_user_status', 'uploaded_by', 'processing_status'),
    )


class Progress(Base):
    """Progress tracking for user-document-chapter combinations."""
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True, index=True)

    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)

    # Chapter/Section tracking
    chapter_number = Column(Integer, nullable=False, index=True)
    chapter_title = Column(String(500))

    # Progress status
    status = Column(String(50), default="not_started", index=True)  # not_started, in_progress, completed, locked
    completion_percentage = Column(Float, default=0.0)

    # Adaptive learning data
    cognitive_level_assigned = Column(Integer)  # L1-L5 level when assigned
    time_spent_minutes = Column(Integer, default=0)
    quiz_attempts = Column(Integer, default=0)
    quiz_success_rate = Column(Float, default=0.0)

    # Timestamps
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    last_accessed_at = Column(DateTime(timezone=True), onupdate=func.now(), index=True)

    __table_args__ = (
        Index('idx_progress_user_document', 'user_id', 'document_id'),
        Index('idx_progress_document_chapter', 'document_id', 'chapter_number'),
        Index('idx_progress_user_chapter', 'user_id', 'document_id', 'chapter_number', unique=True),
        Index('idx_progress_status', 'status', 'completion_percentage'),
    )

    def __repr__(self):
        return f"<Progress(id={self.id}, user_id={self.user_id}, chapter={self.chapter_number}, status={self.status})>"


class ConversationHistory(Base):
    """对话历史记录"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), index=True)
    chapter_number = Column(Integer, index=True)

    # 对话内容
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)

    # 附加数据
    student_level_at_time = Column(Integer)  # 对话时的学生等级
    extra_metadata = Column(Text)  # JSON 格式的额外信息（重命名以避免与 SQLAlchemy 保留字冲突）

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index('idx_conversation_user_doc', 'user_id', 'document_id'),
        Index('idx_conversation_user_chapter', 'user_id', 'document_id', 'chapter_number'),
    )

    def __repr__(self):
        return f"<Conversation(id={self.id}, role={self.role}, user_id={self.user_id})>"


class QuizAttempt(Base):
    """题目尝试记录"""
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    progress_id = Column(Integer, ForeignKey("progress.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)

    # 题目信息
    question_text = Column(Text, nullable=False)
    user_answer = Column(String(500))
    correct_answer = Column(String(500))
    is_correct = Column(Integer, nullable=False, index=True)  # 0 or 1

    # 元数据
    time_spent_seconds = Column(Integer)
    attempts_count = Column(Integer, default=1)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_quiz_user_progress', 'user_id', 'progress_id'),
        Index('idx_quiz_progress_correct', 'progress_id', 'is_correct'),
    )

    def __repr__(self):
        return f"<QuizAttempt(id={self.id}, correct={self.is_correct})>"


class Question(Base):
    """题目数据库模型"""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)

    # 关联文档、章节和小节
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    chapter_number = Column(Integer, nullable=False, index=True)
    subsection_number = Column(String(50), nullable=True, index=True)  # 小节编号，如 "1.1", "1.2"

    # 题目基本信息
    question_type = Column(String(50), nullable=False, index=True)  # 'choice', 'fill_blank', 'essay'
    question_text = Column(Text, nullable=False)

    # 选项（JSON格式，用于选择题）
    # 格式: {"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"}
    options = Column(Text)

    # 答案和解析
    correct_answer = Column(String(500), nullable=False)
    explanation = Column(Text)  # 题目解析

    # 难度和分类
    difficulty = Column(Integer, default=3, index=True)  # 1-5难度
    competency_dimension = Column(String(50), index=True)  # 能力维度: comprehension, logic, terminology, memory, application, stability

    # 元数据
    created_by = Column(String(50), default="AI")  # AI生成或人工创建
    is_active = Column(Integer, default=1, index=True)  # 是否启用

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index('idx_question_doc_chapter', 'document_id', 'chapter_number'),
        Index('idx_question_subsection', 'document_id', 'chapter_number', 'subsection_number'),
        Index('idx_question_type_difficulty', 'question_type', 'difficulty'),
        Index('idx_question_active', 'is_active', 'document_id'),
    )

    def __repr__(self):
        return f"<Question(id={self.id}, type={self.question_type}, chapter={self.chapter_number})>"
