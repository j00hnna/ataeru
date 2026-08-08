"""
نماذج Pydantic للردود.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class ResponseOut(BaseModel):
    id: int
    analysis_id: int
    generated_content: Optional[List[Dict[str, Any]]] = None
    compliance_score: Optional[float] = None
    compliance_details: Optional[List[Dict[str, Any]]] = None
    status: str
    version: int
    final_document_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ResponseUpdate(BaseModel):
    answers: Optional[List[Dict[str, str]]] = None
    generated_content: Optional[str] = None