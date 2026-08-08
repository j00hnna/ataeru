"""
تبعيات FastAPI: المصادقة والصلاحيات.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.auth_service import AuthService
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", scheme_name="JWT")

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    return AuthService.get_current_user(db, token)

def get_current_active_verified_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_verified:
        raise HTTPException(status_code=403, detail="البريد الإلكتروني غير مؤكد")
    return current_user

def require_admin(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="تتطلب صلاحيات المسؤول")
    return current_user

def verify_company_access(company_id: int, current_user: User = Depends(get_current_user)):
    if current_user.company_id != company_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="لا يمكنك الوصول إلى بيانات شركة أخرى")
    return current_user

def check_subscription_quota(required_plan: str = "PRO"):
    def dependency(current_user: User = Depends(get_current_user)):
        company = current_user.company
        if not company:
            raise HTTPException(403, "لا شركة مرتبطة")
        if company.subscription_plan.value == "FREE" and required_plan != "FREE":
            raise HTTPException(403, "هذه الميزة تتطلب اشتراكاً مدفوعاً")
        return current_user
    return dependency