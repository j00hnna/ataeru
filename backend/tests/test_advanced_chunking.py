"""
اختبارات معالج الـ chunking الذكي.
"""
from app.services.advanced_chunking import AdvancedChunker


class TestAdvancedChunker:

    def test_split_by_sentences_arabic(self):
        """اختبار تقسيم الجمل بالعربية."""
        text = "هذا شرط إجباري. هذا شرط آخر؟ وهذا الثالث!"
        sentences = AdvancedChunker.split_by_sentences(text)

        assert len(sentences) >= 3
        assert "شرط إجباري" in sentences[0]

    def test_split_by_sentences_english(self):
        text = "First sentence. Second sentence? Third!"
        sentences = AdvancedChunker.split_by_sentences(text)
        assert len(sentences) == 3

    def test_estimate_tokens(self):
        """اختبار تقدير الـ tokens."""
        text = "هذا نص اختبار"
        tokens = AdvancedChunker.estimate_tokens(text)

        assert tokens > 0
        assert tokens <= 5

    def test_smart_chunk_basic(self):
        """اختبار الـ chunking الأساسي."""
        text = " ".join(["كلمة"] * 10000)
        chunks = AdvancedChunker.smart_chunk(text)

        assert len(chunks) > 1
        assert all("text" in chunk for chunk in chunks)
        assert all("importance" in chunk for chunk in chunks)
        # التداخل (10%) قد يرفع الحجم قليلاً فوق الحد
        assert all(c["tokens"] <= AdvancedChunker.MAX_CHUNK_TOKENS + 500 for c in chunks)

    def test_smart_chunk_small_text(self):
        """نص قصير يُنتج chunk واحد."""
        text = "عطاء بسيط بمواصفات قليلة."
        chunks = AdvancedChunker.smart_chunk(text)
        assert len(chunks) == 1

    def test_score_importance(self):
        """اختبار حساب الأهمية."""
        high_importance = "شرط إجباري و deadline"
        low_importance = "نص عادي بدون كلمات مهمة"

        score_high = AdvancedChunker.score_importance(high_importance)
        score_low = AdvancedChunker.score_importance(low_importance)

        assert score_high > score_low
        assert 0.0 <= score_high <= 1.0

    def test_sort_by_importance(self):
        """الأجزاء الأهم تأتي أولاً."""
        chunks = [
            {"text": "نص", "importance": 0.1},
            {"text": "متطلب إجباري و deadline و ضمان", "importance": 0.9},
            {"text": "نص", "importance": 0.4},
        ]
        sorted_chunks = AdvancedChunker.sort_by_importance(chunks)
        assert sorted_chunks[0]["importance"] == 0.9
        assert sorted_chunks[-1]["importance"] == 0.1

    def test_merge_chunk_results_deduplicates(self):
        """دمج يزيل التكرار ويجمع من جميع الأجزاء."""
        results = [
            {
                "mandatory_requirements": [
                    {"id": 1, "description": "شرط واحد"},
                    {"id": 2, "description": "شرط ثانٍ"},
                ],
                "technical_questions": [{"id": 1, "question": "سؤال واحد؟"}],
                "deadline": "2026-01-01",
            },
            {
                "mandatory_requirements": [
                    {"id": 3, "description": "شرط واحد"},
                ],
                "technical_questions": [{"id": 2, "question": "سؤال جديد؟"}],
                "evaluation_criteria": {"technical_weight": 60, "price_weight": 40},
            },
        ]

        merged = AdvancedChunker.merge_chunk_results(results)

        assert len(merged["mandatory_requirements"]) == 2  # تمت إزالة التكرار
        assert len(merged["technical_questions"]) == 2
        assert merged["deadline"] == "2026-01-01"
        assert merged["evaluation_criteria"]["technical_weight"] == 60
        assert merged["all_chunks_analyzed"] == 2
