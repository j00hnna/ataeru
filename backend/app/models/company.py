"""
نموذج شركة العميل.
"""
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum
from app.core.database import Base

class SubscriptionPlan(str, enum.Enum):
    FREE = "FREE"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    commercial_register = Column(String(100), unique=True, nullable=True)
    tax_number = Column(String(100), unique=True, nullable=True)
    logo_url = Column(String(500), nullable=True)
    subscription_plan = Column(
        SAEnum(SubscriptionPlan, name="subscription_plan_enum", create_type=True),
        default=SubscriptionPlan.FREE,
        nullable=False
    )
    subscription_end_date = Column(DateTime(timezone=True), nullable=True)
    stripe_customer_id = Column(String(255), unique=True, nullable=True)
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