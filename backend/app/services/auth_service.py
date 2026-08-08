"""
خدمة المصادقة: تسجيل، دخول، تحقق من JWT.
"""
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.models.user import User
from app.models.company import Company, SubscriptionPlan
from app.schemas.auth import RegisterRequest, LoginRequest, Token

class AuthService:
    @staticmethod
    def register_user(db: Session, request: RegisterRequest) -> User:
        if db.query(User).filter(User.email == request.email).first():
            raise HTTPException(status_code=409, detail="البريد الإلكتروني مستخدم مسبقاً")
        company = Company(
            name=request.company_name,
            commercial_register=request.commercial_register,
            tax_number=request.tax_number,
            subscription_plan=SubscriptionPlan.FREE
        )
        db.add(company)
        db.flush()
        user = User(
            email=request.email,
            hashed_password=get_password_hash(request.password),
            full_name=request.full_name,
            company_id=company.id,
            is_active=True,
            is_verified=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate(db: Session, request: LoginRequest) -> Optional[User]:
        user = db.query(User).filter(User.email == request.email).first()
        if not user or not verify_password(request.password, user.hashed_password):
            return None
        if not user.is_active:
            raise HTTPException(status_code=403, detail="الحساب غير نشط")
        return user

    @staticmethod
    def create_tokens(user_id: int) -> Token:
        access_token = create_access_token(subject=str(user_id))
        refresh_token = create_refresh_token(subject=str(user_id))
        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

    @staticmethod
    def get_current_user(db: Session, token: str) -> User:
        payload = decode_token(token)
        if payload is None or payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="رمز الوصول غير صالح")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="رمز الوصول غير صالح")
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="المستخدم غير موجود")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="الحساب غير نشط")
        return user