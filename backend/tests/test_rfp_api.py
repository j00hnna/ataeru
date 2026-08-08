"""
اختبارات نقاط نهاية API للعطاءات.
"""
from types import SimpleNamespace

import pytest

from app.models.rfp_analysis import RFPAnalysis


@pytest.fixture
def mock_celery_delay(monkeypatch):
    """استبدال .delay لتفادي الحاجة إلى Redis/worker."""
    import app.api.v1.rfp as rfp_module

    def fake_delay(analysis_id):
        return SimpleNamespace(id="fake-task-id")

    monkeypatch.setattr(rfp_module.process_rfp_analysis, "delay", fake_delay)
    return fake_delay


def test_upload_rfp_success(client, auth_headers, mock_celery_delay, tmp_path):
    """رفع ملف ناجح يُعيد 202 وحالة queued."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("هذا نص اختبار لملف العطاء.", encoding="utf-8")

    with open(test_file, "rb") as f:
        response = client.post(
            "/api/v1/rfp/upload",
            files={"file": ("test.txt", f, "text/plain")},
            headers=auth_headers,
        )

    assert response.status_code == 202
    body = response.json()
    assert "analysis_id" in body
    assert body["status"] == "queued"
    assert "check_status_url" in body


def test_upload_rfp_invalid_type(client, auth_headers, tmp_path):
    """نوع ملف غير مسموح يُعيد 400."""
    test_file = tmp_path / "test.exe"
    test_file.write_bytes(b"MZ...")

    with open(test_file, "rb") as f:
        response = client.post(
            "/api/v1/rfp/upload",
            files={"file": ("test.exe", f)},
            headers=auth_headers,
        )

    assert response.status_code == 400


def test_upload_rfp_file_too_large(client, auth_headers, tmp_path, monkeypatch):
    """ملف يتجاوز الحد الأقصى يُعيد 413."""
    from app.core.config import settings
    monkeypatch.setattr(settings, "MAX_FILE_SIZE", 1024)

    test_file = tmp_path / "large.txt"
    test_file.write_text("x" * 2048)

    with open(test_file, "rb") as f:
        response = client.post(
            "/api/v1/rfp/upload",
            files={"file": ("large.txt", f)},
            headers=auth_headers,
        )

    assert response.status_code == 413


def test_get_analysis_status(client, auth_headers, db, test_user):
    """استعلام حالة تحليل موجود."""
    analysis = RFPAnalysis(
        user_id=test_user.id,
        company_id=test_user.company_id,
        original_file_name="test.pdf",
        original_file_url="/path/to/file",
        status="processing",
        progress=50,
    )
    db.add(analysis)
    db.commit()

    response = client.get(
        f"/api/v1/rfp/status/{analysis.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processing"
    assert body["progress"] == 50


def test_get_analysis_status_company_isolation(client, auth_headers, db):
    """لا يمكن الوصول لتحليل شركة أخرى."""
    analysis = RFPAnalysis(
        user_id=None,
        company_id=9999,
        original_file_name="other.pdf",
        original_file_url="/path/to/file",
    )
    db.add(analysis)
    db.commit()

    response = client.get(
        f"/api/v1/rfp/status/{analysis.id}",
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_get_analysis_status_requires_auth(client, db):
    """بدون رمز يُعيد 401."""
    response = client.get("/api/v1/rfp/status/1")
    assert response.status_code == 401


def test_list_analyses(client, auth_headers, db, test_user):
    """قائمة التحليلات."""
    for i in range(3):
        db.add(RFPAnalysis(
            user_id=test_user.id,
            company_id=test_user.company_id,
            original_file_name=f"file{i}.pdf",
            original_file_url=f"/path/{i}",
            status="completed",
        ))
    db.commit()

    response = client.get("/api/v1/rfp/list", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert len(response.json()["analyses"]) == 3
