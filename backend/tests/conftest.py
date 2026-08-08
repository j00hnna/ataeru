"""
إعدادات الاختبارات: قاعدة بيانات SQLite، مستخدم/شركة، وعميل API.
"""
import os

# يجب تعيين البيئة قبل استيراد وحدات التطبيق
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("AI_PROVIDER", "mock")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-tests-min-32-characters")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.models.company import Company, SubscriptionPlan
from app.models.user import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"])

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """إنشاء جلسة بيانات نظيفة لكل اختبار."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_company(db):
    """إنشاء شركة اختبار."""
    company = Company(
        name="Test Company",
        subscription_plan=SubscriptionPlan.FREE,
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@pytest.fixture
def test_user(db, test_company):
    """إنشاء مستخدم اختبار."""
    user = User(
        email="test@example.com",
        hashed_password=pwd_context.hash("password123"),
        full_name="Test User",
        company_id=test_company.id,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user):
    """رمز وصول JWT حقيقي للمستخدم."""
    return create_access_token(subject=str(test_user.id))


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def client(db):
    """عميل TestClient مع override لـ get_db."""
    from fastapi.testclient import TestClient
    from app.main import app

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def task_db(tmp_path, monkeypatch):
    """قاعدة بيانات SQLite ملفية مشتركة بين الاختبار ومهمة Celery.

    مهمة Celery تفتح اتصالاً مستقلاً (SessionLocal خاص بها)، بينما قواعد
    SQLite في الذاكرة تُحذف عند استبدال الاتصال، لذا تُستخدم قاعدة ملفية.
    """
    from app.core.database import Base

    # استيراد جميع النماذج لتسجيلها في metadata قبل create_all
    import app.main  # noqa: F401

    engine = create_engine(
        f"sqlite:///{tmp_path / 'e2e.db'}",
        connect_args={"check_same_thread": False},
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr("app.core.database.SessionLocal", TestingSession)

    yield TestingSession

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def create_analysis(TestingSession, file_path):
    """إنشاء شركة ومستخدم وتحليل مرتبط بملف نصي ضمن جلسة معطاة."""
    from app.models.company import Company, SubscriptionPlan
    from app.models.user import User
    from app.models.rfp_analysis import RFPAnalysis

    session = TestingSession()
    try:
        company = Company(name="Test Company", subscription_plan=SubscriptionPlan.FREE)
        session.add(company)
        session.commit()

        user = User(
            email="e2e@example.com",
            hashed_password="x",
            full_name="E2E User",
            company_id=company.id,
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        session.commit()

        analysis = RFPAnalysis(
            user_id=user.id,
            company_id=company.id,
            original_file_name=file_path.name,
            original_file_url=str(file_path),
            status="queued",
        )
        session.add(analysis)
        session.commit()
        session.refresh(analysis)
        return session, analysis.id
    except Exception:
        session.close()
        raise
