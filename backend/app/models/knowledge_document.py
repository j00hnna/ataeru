"""
نموذج مستند قاعدة المعرفة.
"""
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class DocumentStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_url = Column(String(1000), nullable=False)
    file_type = Column(String(50), nullable=False)
    status = Column(
        SAEnum(DocumentStatus, name="document_status_enum", create_type=True),
        default=DocumentStatus.UPLOADED,
        nullable=False
    )
    chunk_count = Column(Integer, default=0)
    uploaded_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    company = relationship("Company", backref="knowledge_documents")