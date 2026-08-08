"""
اختبارات خدمة التحليل القوية.
"""
import pytest

from app.services.robust_rfp_service import RobustRFPService, QualityScore


class TestQualityScore:

    def test_calculate_quality_score_excellent(self):
        """نتيجة كاملة تُعطي جودة ممتازة."""
        result = {
            "mandatory_requirements": [
                {"id": 1, "description": "req1"},
                {"id": 2, "description": "req2"},
                {"id": 3, "description": "req3"},
                {"id": 4, "description": "req4"},
                {"id": 5, "description": "req5"},
            ],
            "deadline": "2026-12-31",
            "technical_questions": [
                {"id": 1, "question": "q1"},
                {"id": 2, "question": "q2"},
                {"id": 3, "question": "q3"},
            ],
            "boq_summary": {"total": 1000000},
            "evaluation_criteria": {"technical_weight": 60, "price_weight": 40},
        }

        quality = RobustRFPService.calculate_quality_score(result, "sample")
        assert quality == QualityScore.EXCELLENT

    def test_calculate_quality_score_partial(self):
        """نتيجة جزئية تُعطي جودة مقبولة."""
        result = {
            "mandatory_requirements": [{"id": 1, "description": "req1"}],
            "deadline": "2026-12-31",
        }

        quality = RobustRFPService.calculate_quality_score(result, "sample")
        assert quality in (QualityScore.ACCEPTABLE, QualityScore.POOR)

    def test_calculate_quality_score_failed(self):
        """نتيجة فارغة تُعطي فشل."""
        result = {}
        quality = RobustRFPService.calculate_quality_score(result, "sample")
        assert quality == QualityScore.FAILED

    def test_calculate_confidence(self):
        assert RobustRFPService.calculate_confidence(QualityScore.EXCELLENT) == 95
        assert RobustRFPService.calculate_confidence(QualityScore.GOOD) == 80
        assert RobustRFPService.calculate_confidence(QualityScore.ACCEPTABLE) == 65
        assert RobustRFPService.calculate_confidence(QualityScore.POOR) == 40
        assert RobustRFPService.calculate_confidence(QualityScore.FAILED) == 0


class TestSafeExtractText:

    @pytest.mark.asyncio
    async def test_safe_extract_text_txt(self, tmp_path):
        """استخراج من ملف TXT."""
        txt_path = tmp_path / "test.txt"
        txt_path.write_text("هذا نص اختبار بسيط", encoding="utf-8")

        text = RobustRFPService.safe_extract_text(str(txt_path), "test.txt")
        assert "هذا نص اختبار" in text

    @pytest.mark.asyncio
    async def test_safe_extract_text_pdf(self, tmp_path):
        """استخراج من ملف PDF."""
        from reportlab.pdfgen import canvas

        pdf_path = tmp_path / "test.pdf"
        c = canvas.Canvas(str(pdf_path))
        c.drawString(100, 750, "This is a test PDF")
        c.save()

        text = RobustRFPService.safe_extract_text(str(pdf_path), "test.pdf")
        assert text is not None
        assert len(text) > 0

    @pytest.mark.asyncio
    async def test_safe_extract_text_invalid_format(self, tmp_path):
        """صيغة غير مدعومة ترمي ValueError."""
        bad_path = tmp_path / "file.xyz"
        bad_path.write_text("x")

        with pytest.raises(ValueError):
            RobustRFPService.safe_extract_text(str(bad_path), "file.xyz")

    @pytest.mark.asyncio
    async def test_safe_extract_text_missing_file(self):
        with pytest.raises(ValueError):
            RobustRFPService.safe_extract_text("/nonexistent/file.pdf", "file.pdf")
