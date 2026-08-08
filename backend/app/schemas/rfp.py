"""
مخططات Pydantic لوحدة العطاءات.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class RFPAnalysisOut(BaseModel):
    id: int
    user_id: Optional[int]
    company_id: int
    original_file_name: str
    original_file_url: str
    extracted_text: Optional[str] = None
    extracted_requirements: Optional[Dict[str, Any]] = None
    mandatory_checklist: Optional[List[Dict[str, Any]]] = None
    evaluation_criteria: Optional[Dict[str, Any]] = None
    analysis_result: Optional[Dict[str, Any]] = None
    quality_score: Optional[str] = None
    confidence_score: int = 0
    status: str
    progress: int = 0
    retry_count: int = 0
    current_attempt: int = 0
    error_message: Optional[str] = None
    is_validated: bool = False
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RFPAnalysisUpdate(BaseModel):
    extracted_requirements: Optional[Dict[str, Any]] = None
    mandatory_checklist: Optional[List[Dict[str, Any]]] = None
    evaluation_criteria: Optional[Dict[str, Any]] = None
