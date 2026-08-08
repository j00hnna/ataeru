"""
اختبارات تدفق الردود: توليد → تدقيق امتثال → تصدير.
تُشغّل كاملة بوضع المحاكاة (AI_PROVIDER=mock) دون أي Fake Provider.
"""
from app.models.response import Response as ResponseModel, ResponseStatus
from app.services.export_service import ExportService
from tests.conftest import create_analysis


def run_analysis(task_db, tmp_path):
    """تشغيل التحليل فعلياً وإرجاع (session, analysis_id)."""
    from celery_app import process_rfp_analysis

    text = (
        "هذا عطاء لتنفيذ مشروع إنشاء مدرسة ابتدائية بمنطقة الرياض.\n"
        "يجب أن يكون المقاول مسجلاً لدى الهيئة السعودية للمقاولين.\n"
        "يشترط تقديم شهادة السجل التجاري سارية المفعول.\n"
        "السؤال الفني الأول: وضح منهجية تنفيذ الأعمال الإنشائية.\n"
        "السؤال الفني الثاني: قدم خطة زمنية لإنجاز المشروع خلال 18 شهراً.\n"
        "كما يشترط تقديم ضمان ابتدائي بنسبة 5% من قيمة العطاء.\n"
    )
    file_path = tmp_path / "rfp.txt"
    file_path.write_text(text, encoding="utf-8")

    session, analysis_id = create_analysis(task_db, file_path)
    result = process_rfp_analysis.run(analysis_id)
    assert result["success"] is True
    return session, analysis_id


def test_response_generate_and_compliance(task_db, tmp_path):
    """توليد الرد ثم تدقيق الامتثال يملأ درجة الامتثال ويحدّث الحالة."""
    from app.services.response_generator import ResponseGenerator

    session, analysis_id = run_analysis(task_db, tmp_path)

    response = ResponseGenerator.generate_full_response(analysis_id, session)

    assert response.status == ResponseStatus.DRAFT
    assert isinstance(response.generated_content, list)
    assert len(response.generated_content) >= 1
    assert all(a.get("question") and a.get("answer") for a in response.generated_content)

    from app.services.compliance_checker import ComplianceChecker

    checked = ComplianceChecker.run_compliance_check(analysis_id, session)

    assert checked.compliance_score is not None
    assert 0 <= checked.compliance_score <= 100
    assert checked.status == ResponseStatus.REVIEWED
    assert checked.compliance_details is not None
    assert len(checked.compliance_details) == len(checked.analysis.mandatory_checklist or [])
    session.close()


def test_response_export_after_full_compliance(task_db, tmp_path):
    """التصدير يتطلب اكتمال التحليل والرد والامتثال 100%."""
    from app.services.response_generator import ResponseGenerator
    from app.services.compliance_checker import ComplianceChecker

    session, analysis_id = run_analysis(task_db, tmp_path)

    ResponseGenerator.generate_full_response(analysis_id, session)
    checked = ComplianceChecker.run_compliance_check(analysis_id, session)

    # في وضع المحاكاة يغطي المزود كل الشروط → امتثال كامل
    assert checked.compliance_score == 100.0

    response = session.query(ResponseModel).get(checked.id)
    export_path = ExportService.export(response, "docx")
    assert str(export_path).endswith(".docx")
    import os
    assert os.path.exists(export_path)
    session.close()
