"""
خدمة تدقيق الامتثال.
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.rfp_analysis import RFPAnalysis
from app.models.response import Response, ResponseStatus
from app.services.ai_provider import get_ai_provider

CHECK_PROMPT = """
أنت مدقق جودة. تحقق مما إذا كان الرد يغطي الشرط الإجباري التالي.
الشرط: {requirement}
نص الرد (ملخص): {response_summary}
أجب فقط بـ "نعم" إذا كان الشرط مغطى، وإلا "لا"، ثم أضف تعليل قصير بعد فاصلة منقوطة (;).
مثال: نعم; تم ذكر الخبرة المطلوبة
"""

class ComplianceChecker:
    @staticmethod
    def _check_single(requirement: str, response_summary: str) -> Dict[str, Any]:
        ai = get_ai_provider()
        prompt = CHECK_PROMPT.format(requirement=requirement, response_summary=response_summary[:2000])
        messages = [{"role": "user", "content": prompt}]
        try:
            result = ai.generate_completion(messages, temperature=0.0, max_tokens=100)
            parts = result.split(";")
            met = "نعم" in parts[0]
            reasoning = parts[1].strip() if len(parts) > 1 else result
            return {"met": met, "reasoning": reasoning}
        except Exception:
            return {"met": False, "reasoning": "تعذر التحقق"}

    @staticmethod
    def run_compliance_check(analysis_id: int, db: Session) -> Response:
        analysis = db.query(RFPAnalysis).filter(RFPAnalysis.id == analysis_id).first()
        if not analysis:
            raise ValueError("التحليل غير موجود")
        if not analysis.mandatory_checklist:
            raise ValueError("لا توجد شروط إجبارية")
        response = db.query(Response).filter(Response.analysis_id == analysis_id).first()
        if not response or not response.generated_content:
            raise ValueError("لا يوجد رد مولّد")

        # دمج الإجابات في نص واحد
        answers = response.generated_content
        if isinstance(answers, list):
            combined = "\n".join([f"Q: {a.get('question','')}\nA: {a.get('answer','')}" for a in answers])
        else:
            combined = str(answers)

        checklist = analysis.mandatory_checklist
        results = []
        met_count = 0
        for item in checklist:
            desc = item.get("description", "")
            check = ComplianceChecker._check_single(desc, combined)
            results.append({
                "requirement_id": item.get("id"),
                "description": desc,
                "met": check["met"],
                "reasoning": check["reasoning"]
            })
            if check["met"]:
                met_count += 1

        score = (met_count / len(checklist)) * 100 if checklist else 100.0
        response.compliance_score = score
        response.compliance_details = results
        response.status = ResponseStatus.REVIEWED
        db.commit()
        db.refresh(response)
        return response