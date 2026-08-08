"""
مخططات Pydantic لوحدة قاعدة المعرفة.
"""
from datetime import datetime
from pydantic import BaseModel

class KnowledgeDocumentOut(BaseModel):
    id: int
    file_name: str
    file_url: str
    file_type: str
    status: str
    chunk_count: int
    uploaded_at: datetime

    class Config:
        from_attributes = True

class DocumentChunkOut(BaseModel):
    id: int
    document_id: int
    chunk_text: str
    chunk_index: int

    class Config:
        from_attributes = True