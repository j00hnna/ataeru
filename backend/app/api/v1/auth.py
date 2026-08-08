"""
نقاط نهاية API للمصادقة: التسجيل، الدخول، تحديث الرمز، معلومات المستخدم.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import RegisterRequest, Token, LoginRequest
from app.schemas.user import UserOut
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["المصادقة"])


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="تسجيل حساب جديد",
    description="إنشاء حساب مستخدم جديد مع شركة افتراضية تلقائياً"
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    تسجيل مستخدم جديد:
    - التحقق من فريدة البريد الإلكتروني والسجل التجاري
    - تشفير كلمة المرور
    - إنشاء شركة ومستخدم مرتبطين
    """
    try:
        user = AuthService.register(db, request)
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="حدث خطأ أثناء التسجيل، يرجى المحاولة لاحقاً"
        )


@router.post(
    "/login",
    response_model=Token,
    summary="تسجيل الدخول",
    description="إدخال البريد الإلكتروني وكلمة المرور للحصول على رموز الوصول"
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    تسجيل الدخول وإرجاع رموز JWT.
    """
    user = AuthService.authenticate(db, request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="البريد الإلكتروني أو كلمة المرور غير صحيحة"
        )
    return AuthService.create_tokens(user.id)


@router.post(
    "/refresh",
    response_model=Token,
    summary="تحديث رمز الوصول",
    description="استخدام رمز التحديث للحصول على رمز وصول جديد"
)
def refresh_token(
    refresh_token: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """
    تحديث رمز الوصول باستخدام رمز التحديث.
    لا يتطلب التحقق من صحة المستخدم في قاعدة البيانات بشكل كبير.
    """
    try:
        return AuthService.refresh_access_token(refresh_token)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="تعذر تحديث الرمز"
        )


@router.get(
    "/me",
    response_model=UserOut,
    summary="معلومات المستخدم الحالي",
    description="إرجاع بيانات المستخدم المصادق عليه حالياً مع بيانات الشركة"
)
def read_users_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    عرض بيانات المستخدم المسجل دخوله حالياً.
    يتم جلب المستخدم مع علاقاته (مثل الشركة) لضمان اكتمال البيانات.
    """
    # إعادة جلب المستخدم من قاعدة البيانات مع تحميل علاقة الشركة
    user = db.query(User).options(joinedload(User.company)).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )
    return user
