"""
اختبارات شاملة لمسار المعالجة غير المتزامنة (مهمة Celery + الخدمة القوية).
"""
import asyncio
import json

import pytest

from app.models.rfp_analysis import RFPAnalysis
from tests.conftest import create_analysis

SAMPLE_TEXT = """
هذا عطاء لتنفيذ مشروع إنشاء مدرسة ابتدائية بمنطقة الرياض.
يجب أن يكون المقاول مسجلاً لدى الهيئة السعودية للمقاولين.
يشترط تقديم شهادة السجل التجاري سارية المفعول.
آخر موعد لتقديم العروض هو 2026-10-15 الساعة 2 ظهراً.
يتم التقييم وفق المعايير التالية: الجانب الفني 70% والسعر 30%.
السؤال الفني الأول: وضح منهجية تنفيذ الأعمال الإنشائية.
السؤال الفني الثاني: قدم خطة زمنية لإنجاز المشروع خلال 18 شهراً.
تتضمن وثائق العطاء جدول كميات بأعمال الحفر والخرسانة والتشطيب.
كما يشترط تقديم ضمان ابتدائي بنسبة 5% من قيمة العطاء.
"""

VALID_JSON = {
    "mandatory_requirements": [
        {"description": "التسجيل في الهيئة السعودية للمقاولين", "is_mandatory": True},
        {"description": "سجل تجاري ساري المفعول", "is_mandatory": True},
        {"description": "تقديم ضمان ابتدائي بنسبة 5%", "is_mandatory": True},
        {"description": "تسليم الجدول الزمني", "is_mandatory": False},
    ],
    "deadline": "2026-10-15",
    "evaluation_criteria": {"technical_weight": 70, "price_weight": 30},
    "technical_questions": [
        {"question": "وضح منهجية تنفيذ الأعمال الإنشائية"},
        {"question": "قدم خطة زمنية لإنجاز المشروع"},
    ],
    "boq_summary": {"total_estimated_value": "غير محدد", "items": ["أعمال الحفر", "الخرسانة", "التشطيب"]},
}


class FakeJsonProvider:
    def generate_completion(self, messages, temperature=0.3, max_tokens=4000):
        return json.dumps(VALID_JSON, ensure_ascii=False)


@pytest.fixture
def fake_json_provider(monkeypatch):
    import app.services.robust_rfp_service as service_module
    monkeypatch.setattr(service_module, "get_ai_provider", lambda: FakeJsonProvider())


class GarbageProvider:
    def generate_completion(self, messages, temperature=0.3, max_tokens=4000):
        return "هذا رد غير صالح وغير قابل للتحليل JSON على الإطلاق."


def test_process_rfp_analysis_success_end_to_end(task_db, tmp_path, fake_json_provider):
    """مسار النجاح الكامل: ملف → استخراج → تقسيم → LLM → دمج → جودة → completed."""
    file_path = tmp_path / "rfp.txt"
    file_path.write_text(SAMPLE_TEXT, encoding="utf-8")

    session, analysis_id = create_analysis(task_db, file_path)

    from celery_app import process_rfp_analysis

    result = process_rfp_analysis.run(analysis_id)

    assert result["success"] is True
    assert result["analysis_id"] == analysis_id

    analysis = session.query(RFPAnalysis).get(analysis_id)
    assert analysis.status == "completed"
    assert analysis.quality_score in ("excellent", "good", "acceptable")
    assert analysis.confidence_score > 0
    assert analysis.progress == 100
    assert analysis.completed_at is not None
    assert analysis.extracted_requirements is not None
    assert len(analysis.mandatory_checklist) == 4
    assert analysis.evaluation_criteria.get("technical_weight") == 70
    assert len(analysis.extracted_requirements["technical_questions"]) == 2
    session.close()


def test_process_rfp_analysis_failure_end_to_end(task_db, tmp_path, monkeypatch):
    """مسار الفشل: LLM يُرجع نصاً غير صالح → retry → حالة failed مع رسالة خطأ."""
    import app.services.robust_rfp_service as service_module
    monkeypatch.setattr(service_module, "get_ai_provider", lambda: GarbageProvider())

    file_path = tmp_path / "rfp.txt"
    file_path.write_text(SAMPLE_TEXT, encoding="utf-8")

    session, analysis_id = create_analysis(task_db, file_path)

    from app.services.robust_rfp_service import RobustRFPService

    result = asyncio.run(RobustRFPService.extract_and_analyze_robust(session, analysis_id))

    assert result["success"] is False
    analysis = session.query(RFPAnalysis).get(analysis_id)
    assert analysis.status == "failed"
    assert analysis.error_message
    assert analysis.quality_score == "failed"
    assert analysis.confidence_score == 0
    session.close()


def test_mock_provider_full_pipeline(task_db, tmp_path):
    """وضع المحاكاة (بدون مفتاح OpenAI): يجب أن يكتمل التحليل فعلياً بنجاح."""
    from app.services.ai_provider import MockProvider

    result = MockProvider().generate_completion([
        {"role": "user", "content": "نص عطاء. أعد الرد بصيغة JSON صارمة. السؤال الفني: وضح المنهجية."}
    ])
    assert isinstance(json.loads(result), dict)

    file_path = tmp_path / "rfp.txt"
    file_path.write_text(SAMPLE_TEXT, encoding="utf-8")

    session, analysis_id = create_analysis(task_db, file_path)

    from celery_app import process_rfp_analysis

    task_result = process_rfp_analysis.run(analysis_id)

    assert task_result["success"] is True
    analysis = session.query(RFPAnalysis).get(analysis_id)
    assert analysis.status == "completed"
    assert analysis.extracted_requirements.get("mandatory_requirements")
    session.close()
