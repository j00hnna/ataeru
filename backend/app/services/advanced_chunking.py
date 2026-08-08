"""
معالج chunking ذكي للملفات الكبيرة مع حفظ السياق والتداخل.
"""
from typing import List, Dict
import re

class AdvancedChunker:
    """معالج chunking ذكي للملفات الكبيرة."""

    MAX_CHUNK_TOKENS = 3000  # ~10,000 حرف
    OVERLAP_TOKENS = 200
    OVERLAP_RATIO = 0.1  # 10% تداخل بين الأجزاء

    KEYWORDS = [
        "متطلب إجباري", "deadline", "شرط", "عقوبة",
        "معايير التقييم", "الدفع", "الموعد", "ضمان",
        "مواصفات", "جودة", "سعر", "الكمية",
        "mandatory", "requirement", "deadline", "payment",
    ]

    @staticmethod
    def split_by_sentences(text: str) -> List[str]:
        """تقسيم النص بناءً على الجمل (عربي وإنجليزي)."""
        pattern = r'(?<=[.!?؟!\n])\s+'
        sentences = re.split(pattern, text)
        return [s.strip() for s in sentences if s.strip()]

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """تقدير عدد tokens (1 كلمة ≈ 1.3 token)."""
        words = len(text.split())
        return int(words * 1.3)

    WORD_TOKEN_ESTIMATE = 1.3

    @staticmethod
    def _split_long_sentence(sentence: str) -> List[str]:
        """تقسيم جملة طويلة جداً إلى أجزاء ضمن حد الـ tokens."""
        words = sentence.split()
        pieces = []
        current = []
        current_tokens = 0.0

        for word in words:
            if current and current_tokens + AdvancedChunker.WORD_TOKEN_ESTIMATE > AdvancedChunker.MAX_CHUNK_TOKENS:
                pieces.append(" ".join(current))
                current = []
                current_tokens = 0.0
            current.append(word)
            current_tokens += AdvancedChunker.WORD_TOKEN_ESTIMATE

        if current:
            pieces.append(" ".join(current))

        return pieces or [sentence]

    @staticmethod
    def smart_chunk(text: str) -> List[Dict]:
        """تقسيم النص بذكاء مع الحفاظ على السياق وتداخل الأجزاء."""
        # جمّل طويلة جداً تُقسَّم مسبقاً لتجنب تجاوز حد الـ tokens
        units: List[str] = []
        for sentence in AdvancedChunker.split_by_sentences(text):
            if AdvancedChunker.estimate_tokens(sentence) > AdvancedChunker.MAX_CHUNK_TOKENS:
                units.extend(AdvancedChunker._split_long_sentence(sentence))
            else:
                units.append(sentence)

        chunks = []
        current_chunk: List[str] = []
        current_tokens = 0

        for sentence in units:
            sentence_tokens = AdvancedChunker.estimate_tokens(sentence)

            if current_tokens + sentence_tokens > AdvancedChunker.MAX_CHUNK_TOKENS:
                if current_chunk:  # احفظ الـ chunk الحالي
                    chunk_text = " ".join(current_chunk)
                    chunks.append({
                        "text": chunk_text,
                        "tokens": current_tokens,
                        "index": len(chunks),
                        "importance": AdvancedChunker.score_importance(chunk_text),
                    })
                    # ابدأ chunk جديد مع تداخل محسوب بالـ tokens (نسبة من حجم الـ chunk)
                    target_overlap = max(int(current_tokens * AdvancedChunker.OVERLAP_RATIO), 0)
                    overlap_words = []
                    overlap_tokens = 0
                    for word in reversed(chunk_text.split()):
                        if overlap_words and overlap_tokens + 1 > target_overlap:
                            break
                        overlap_words.insert(0, word)
                        overlap_tokens += 1
                    current_chunk = [" ".join(overlap_words)]
                    current_tokens = overlap_tokens

            current_chunk.append(sentence)
            current_tokens += sentence_tokens

        # أضف الـ chunk الأخير
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "tokens": current_tokens,
                "index": len(chunks),
                "importance": AdvancedChunker.score_importance(chunk_text),
            })

        return chunks

    @staticmethod
    def sort_by_importance(chunks: List[Dict]) -> List[Dict]:
        """فرز الأجزاء حسب الأهمية تنازلياً (تحليل الأهم أولاً)."""
        return sorted(chunks, key=lambda c: c.get("importance", 0), reverse=True)

    @staticmethod
    def score_importance(text: str) -> float:
        """حساب أهمية النص (0-1)."""
        lowered = text.lower()
        score = sum(1 for kw in AdvancedChunker.KEYWORDS if kw in lowered)
        return min(score / len(AdvancedChunker.KEYWORDS), 1.0)

    @staticmethod
    def merge_chunk_results(chunk_results: List[Dict]) -> Dict:
        """دمج نتائج تحليل الـ chunks مع إزالة التكرار."""
        merged = {
            "mandatory_requirements": [],
            "technical_questions": [],
            "deadline": None,
            "evaluation_criteria": None,
            "boq_summary": None,
            "all_chunks_analyzed": len(chunk_results),
        }

        # دمج المتطلبات من جميع الـ chunks
        seen_reqs = set()
        for chunk_result in chunk_results:
            if "mandatory_requirements" in chunk_result:
                for req in chunk_result["mandatory_requirements"]:
                    req_text = str(req.get("description", "")).lower()
                    if req_text and req_text not in seen_reqs:
                        merged["mandatory_requirements"].append(req)
                        seen_reqs.add(req_text)

        # دمج الأسئلة
        seen_questions = set()
        for chunk_result in chunk_results:
            if "technical_questions" in chunk_result:
                for q in chunk_result["technical_questions"]:
                    q_text = str(q.get("question", "")).lower()
                    if q_text and q_text not in seen_questions:
                        merged["technical_questions"].append(q)
                        seen_questions.add(q_text)

        # خذ أول deadline وأول evaluation_criteria و boq_summary
        for chunk_result in chunk_results:
            if not merged["deadline"] and "deadline" in chunk_result:
                merged["deadline"] = chunk_result["deadline"]
            if not merged["evaluation_criteria"] and "evaluation_criteria" in chunk_result:
                merged["evaluation_criteria"] = chunk_result["evaluation_criteria"]
            if not merged["boq_summary"] and "boq_summary" in chunk_result:
                merged["boq_summary"] = chunk_result["boq_summary"]

        return merged
