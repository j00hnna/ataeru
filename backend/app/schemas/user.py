"""
مخططات Pydantic لعرض بيانات المستخدم والشركة.
"""
from datetime import datetime
from pydantic import BaseModel


class CompanyOut(BaseModel):
    """بيانات الشركة التي تُعرض للمستخدم."""
    id: int
    name: str
    commercial_register: str | None
    tax_number: str | None
    logo_url: str | None
    subscription_plan: str
    subscription_end_date: datetime | None
    
    class Config:
        from_attributes = True


class UserOut(BaseModel):
    """بيانات المستخدم التي تُعرض بعد المصادقة."""
    id: int
    email: str
    full_name: str
    is_active: bool
    is_verified: bool
    company: CompanyOut | None
    created_at: datetime
    
    class Config:
        from_attributes = True