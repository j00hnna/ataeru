"""
نقاط نهاية تحليلات العميل.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["تحليلاتي"])


@router.get("")
def get_my_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    عرض تحليلات العميل الحالي.
    """
    return AnalyticsService.get_client_analytics(db, current_user.company_id)