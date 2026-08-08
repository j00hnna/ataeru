"""
نموذج تحليل العطاء.
"""
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SAEnum, Text, Boolean, JSON, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base

class AnalysisStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"

class RFPAnalysis(Base):
    __tablename__ = "rfp_analyses"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # File Info
    original_file_name = Column(String(255), nullable=False)
    original_file_url = Column(String(1000), nullable=False)
    extracted_text = Column(Text, nullable=True)

    # Analysis Results (حقول التوافق القديمة تُبقى للخدمات الأخرى)
    extracted_requirements = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    mandatory_checklist = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    evaluation_criteria = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)

    # Analysis Results (المرجع الرسمي)
    analysis_result = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    quality_score = Column(String(50), nullable=True)  # excellent, good, acceptable, poor, failed
    confidence_score = Column(Integer, default=0, nullable=False)  # 0-100

    # Status Tracking
    status = Column(
        SAEnum(AnalysisStatus, name="analysis_status_enum", create_type=True),
        default=AnalysisStatus.QUEUED,
        nullable=False
    )
    progress = Column(Integer, default=0, nullable=False)  # 0-100
    current_attempt = Column(Integer, default=0, nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)

    # Error Handling
    error_message = Column(Text, nullable=True)
    attempt_logs = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)

    # Human Review
    is_validated = Column(Boolean, default=False, nullable=False)
    validator_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    validation_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Celery Task
    celery_task_id = Column(String(255), nullable=True, index=True)

    __table_args__ = (
        Index("idx_user_status", "user_id", "status"),
        Index("idx_quality_score", "quality_score"),
        Index("idx_company_created", "company_id", "created_at"),
    )

    response = relationship("Response", back_populates="analysis", uselist=False, cascade="all, delete-orphan")
    company = relationship("Company", backref="rfp_analyses")
    user = relationship("User", backref="rfp_analyses", foreign_keys=[user_id])
    validator = relationship("User", foreign_keys=[validator_id])
