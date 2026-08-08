"""
نقاط نهاية لوحة تحكم المسؤول (للإداريين فقط).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import require_admin
from app.models.user import User
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["المسؤول"])


@router.get("/stats")
def get_admin_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    عرض إحصائيات عامة للمنصة.
    """
    return AdminService.get_stats(db)


@router.get("/recent-analyses")
def get_recent_analyses(
    limit: int = 10,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    عرض أحدث تحليلات العطاءات.
    """
    return AdminService.get_recent_analyses(db, limit)