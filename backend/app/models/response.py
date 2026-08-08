"""
نموذج الرد الناتج عن تحليل العطاء.
"""
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SAEnum, Float, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base

class ResponseStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    REVIEWED = "REVIEWED"
    EXPORTED = "EXPORTED"

class Response(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("rfp_analyses.id", ondelete="CASCADE"), unique=True, nullable=False)
    generated_content = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    compliance_score = Column(Float, nullable=True)
    compliance_details = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    status = Column(
        SAEnum(ResponseStatus, name="response_status_enum", create_type=True),
        default=ResponseStatus.DRAFT,
        nullable=False
    )
    final_document_url = Column(String(1000), nullable=True)
    version = Column(Integer, default=1)
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

    analysis = relationship("RFPAnalysis", back_populates="response")