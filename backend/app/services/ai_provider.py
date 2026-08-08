"""
طبقة تجريد لمزودي الذكاء الاصطناعي (OpenAI + Mock).
"""
import os
import re
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict
import openai

logger = logging.getLogger("ataeru.ai")

class AIProvider(ABC):
    @abstractmethod
    def generate_completion(self, messages: List[Dict[str, str]], temperature: float = 0.3, max_tokens: int = 4000) -> str:
        pass

class OpenAIProvider(AIProvider):
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY غير معرّف")
        self.client = openai.OpenAI(api_key=api_key)

    def generate_completion(self, messages: List[Dict[str, str]], temperature: float = 0.3, max_tokens: int = 4000) -> str:
        try:
            response = self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

class MockProvider(AIProvider):
    """
    مزود وهمي للتطوير والاختبارات.

    يكتشف سياق الطلب من آخر رسالة ويُعيد نتائج صالحة:
    - تحليل chunks: JSON مطابق لمخطط الاستخراج.
    - تدقيق الامتثال: "نعم/لا; تعليل".
    - توليد الردود: نص رد احترافي.
    """

    _MANDATORY_KEYWORDS = ["ضمان", "سجل تجاري", "ترخيص", "تسجيل", "شهادة", "تأمين", "خبرة", "تصنيف"]
    _QUESTION_HINTS = ["السؤال", "وضح", "قدم خطة", "اشرح", "أذكر", "بيّن"]

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        parts = re.split(r"(?<=[.\n؛؟?])", text)
        return [p.strip() for p in parts if p.strip()]

    def _mock_analysis_result(self, text: str) -> Dict:
        deadline = None
        m = re.search(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}", text)
        if m:
            deadline = m.group(0)

        mandatory = []
        for sentence in self._split_sentences(text):
            if any(kw in sentence for kw in self._MANDATORY_KEYWORDS):
                mandatory.append({"description": sentence[:150], "is_mandatory": True})
            if len(mandatory) >= 5:
                break

        questions = []
        for sentence in self._split_sentences(text):
            if any(h in sentence for h in self._QUESTION_HINTS) and "?" not in sentence[:1]:
                q = sentence[:150]
                if q not in [x["question"] for x in questions]:
                    questions.append({"question": q})
            if len(questions) >= 3:
                break

        return {
            "mandatory_requirements": mandatory or [
                {"description": "تقديم ضمان بنكي ابتدائي", "is_mandatory": True}
            ],
            "deadline": deadline,
            "evaluation_criteria": {"technical_weight": 70, "price_weight": 30},
            "technical_questions": questions or [
                {"question": "اشرح منهجية تنفيذ المشروع والجدول الزمني المقترح."}
            ],
            "boq_summary": {"total_estimated_value": None, "items": []},
        }

    def _mock_answer(self, prompt: str) -> str:
        m = re.search(r"السؤال الفني:\n(.*?)\n\n", prompt, re.DOTALL)
        question = m.group(1).strip() if m else "السؤال الفني المطلوب"
        return (
            f"بالإشارة إلى السؤال: {question}\n\n"
            "نؤكد التزامنا بتقديم حل متكامل وفق أعلى المعايير الفنية والمواصفات "
            "الواردة في وثائق العطاء. سنقوم بتجهيز فريق فني مؤهل، وجدول زمني واضح "
            "للمراحل التنفيذية، مع الاستشهاد بخبرتنا في مشاريع مماثلة وضمان الجودة "
            "وسلامة العمليات. (رد تجريبي من وضع المحاكاة)"
        )

    def generate_completion(self, messages: List[Dict[str, str]], temperature: float = 0.3, max_tokens: int = 4000) -> str:
        last_user = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
        if not last_user:
            return "نعم; تمت تغطية الشرط."

        if "أعد الرد بصيغة JSON" in last_user:
            return json.dumps(self._mock_analysis_result(last_user), ensure_ascii=False)

        if "أجب فقط" in last_user:
            return "نعم; تمت تغطية الشرط في الرد المقدم."

        return self._mock_answer(last_user)

def get_ai_provider() -> AIProvider:
    provider_name = os.getenv("AI_PROVIDER", "openai").lower()
    if provider_name == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            logger.warning(
                "OPENAI_API_KEY غير معرّف — سيتم استخدام المزود الوهمي (mock) "
                "لتشغيل التطبيق محلياً. اضبط المفتاح لتفعيل الذكاء الاصطناعي الحقيقي."
            )
            return MockProvider()
        return OpenAIProvider()
    elif provider_name == "mock":
        return MockProvider()
    else:
        raise ValueError(f"AI provider غير معروف: {provider_name}")
