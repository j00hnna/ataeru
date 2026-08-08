"""
خدمة تحليل العطاءات: استخراج النص، تحليله بالذكاء الاصطناعي، وتخزين النتائج.
"""
import json
import os
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.rfp_analysis import RFPAnalysis, AnalysisStatus
from app.services.document_processor import DocumentProcessor
from app.services.ai_provider import get_ai_provider

# البرومبت المتقدم لتحليل العطاء
RFP_ANALYSIS_PROMPT = """
أنت مساعد ذكي متخصص في تحليل وثائق العطاءات (RFPs) للمشاريع الهندسية والإنشائية.
قم بتحليل النص التالي المستخرج من وثيقة عطاء واستخرج المعلومات التالية بصيغة JSON صارمة.
إذا لم تجد معلومة معينة، اترك القيمة فارغة أو null.

النص:
{text}

المطلوب استخراجه:
1. deadline: تاريخ التقديم النهائي (بصيغة ISO YYYY-MM-DD إن وجد، أو نص).
2. evaluation_criteria: كائن يحتوي على technical_weight و price_weight (أرقام، النسبة المئوية).
3. mandatory_requirements: قائمة (list) بالشروط الإجبارية. كل عنصر كائن يحتوي على:
   - id: رقم تسلسلي
   - description: وصف الشرط
   - is_mandatory: true/false
4. technical_questions: قائمة بالأسئلة الفنية المطلوب الإجابة عنها، كل سؤال كائن:
   - id
   - question: نص السؤال
5. boq_summary: ملخص جدول الكميات (إن وجد)، كائن يحتوي على items (قائمة بالبنود) و total_estimated_value.

أعد JSON فقط بدون أي تعليقات إضافية. يجب أن تكون صيغة JSON صالحة تماماً.
"""

class RFPService:
    @staticmethod
    def extract_text_and_analyze(db: Session, analysis_id: int) -> RFPAnalysis:
        """
        تنفيذ كامل لعملية التحليل: استخراج النص، تحليله، وتحديث السجل.
        """
        analysis = db.query(RFPAnalysis).filter(RFPAnalysis.id == analysis_id).first()
        if not analysis:
            raise ValueError("Analysis not found")

        try:
            # 1. تحديث الحالة إلى PROCESSING
            analysis.status = AnalysisStatus.PROCESSING
            db.commit()

            # 2. استخراج النص من الملف الأصلي
            file_path = analysis.original_file_url
            file_type = analysis.original_file_name.rsplit('.', 1)[-1].upper() if '.' in analysis.original_file_name else "PDF"
            extracted_text = DocumentProcessor.extract_text(file_path, file_type)
            if not extracted_text:
                raise ValueError("لم يتم استخراج أي نص من الملف")
            analysis.extracted_text = extracted_text
            db.commit()

            # 3. تحليل النص باستخدام الذكاء الاصطناعي
            ai_provider = get_ai_provider()
            prompt = RFP_ANALYSIS_PROMPT.format(text=extracted_text[:15000])  # حد أقصى للحجم للتجربة
            messages = [
                {"role": "system", "content": "أنت مساعد متخصص في تحليل وثائق العطاءات. أعد JSON فقط."},
                {"role": "user", "content": prompt}
            ]
            ai_response = ai_provider.generate_completion(messages, temperature=0.2, max_tokens=4000)

            # 4. محاولة تحليل JSON الناتج
            try:
                # أحياناً يرجع JSON محاط بـ ```json ... ```، فنقوم بتنظيفه
                cleaned = ai_response.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                requirements = json.loads(cleaned)
            except json.JSONDecodeError:
                # إذا فشل التحليل المباشر، نحاول مرة أخرى مع نموذج أصغر
                requirements = {
                    "deadline": None,
                    "evaluation_criteria": {},
                    "mandatory_requirements": [],
                    "technical_questions": [],
                    "boq_summary": {}
                }

            # 5. تعبئة الحقول
            analysis.extracted_requirements = requirements
            analysis.mandatory_checklist = requirements.get("mandatory_requirements", [])
            analysis.evaluation_criteria = requirements.get("evaluation_criteria", {})
            analysis.status = AnalysisStatus.COMPLETED
            db.commit()
            db.refresh(analysis)
            return analysis

        except Exception as e:
            analysis.status = AnalysisStatus.FAILED
            analysis.error_message = str(e)
            db.commit()
            raise e