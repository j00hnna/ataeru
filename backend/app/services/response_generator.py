"""
توليد الردود باستخدام AI و RAG.
يخزّن الناتج كـ JSONB (قائمة أسئلة/أجوبة).
"""
import json
from sqlalchemy.orm import Session
from app.models.rfp_analysis import RFPAnalysis
from app.models.response import Response, ResponseStatus
from app.services.ai_provider import get_ai_provider
from app.services.rag_service import RAGService

ANSWER_PROMPT = """
أنت خبير استشاري متخصص في كتابة الردود على العطاءات الهندسية.
استخدم السياق التالي من قاعدة معارف الشركة لصياغة رد احترافي على السؤال الفني.

السؤال الفني:
{question}

السياق من قاعدة المعرفة:
{context}

التعليمات:
- رد احترافي ومقنع.
- استشهد بمشاريع سابقة إن وجدت.
- اللغة العربية الفصحى مع إمكانية مصطلحات إنجليزية.
- الحد الأقصى 500 كلمة.

الرد:
"""

class ResponseGenerator:
    @staticmethod
    def _generate_single_answer(question: str, db: Session, company_id: int) -> str:
        context = RAGService.retrieve_context(query=question, db=db, company_id=company_id)
        prompt = ANSWER_PROMPT.format(question=question, context=context)
        messages = [
            {"role": "system", "content": "أنت خبير استشاري متخصص في كتابة ردود العطاءات."},
            {"role": "user", "content": prompt}
        ]
        ai = get_ai_provider()
        return ai.generate_completion(messages, temperature=0.4, max_tokens=1000)

    @staticmethod
    def generate_full_response(analysis_id: int, db: Session) -> Response:
        analysis = db.query(RFPAnalysis).filter(RFPAnalysis.id == analysis_id).first()
        if not analysis:
            raise ValueError("التحليل غير موجود")
        if not analysis.extracted_requirements:
            raise ValueError("لا توجد متطلبات مستخرجة")
        questions = analysis.extracted_requirements.get("technical_questions", [])
        if not questions:
            raise ValueError("لا توجد أسئلة فنية")

        answers = []
        for q in questions:
            q_text = q.get("question", "")
            if not q_text:
                continue
            ans = ResponseGenerator._generate_single_answer(q_text, db, analysis.company_id)
            answers.append({"question": q_text, "answer": ans})

        response = db.query(Response).filter(Response.analysis_id == analysis_id).first()
        if response:
            response.generated_content = answers
            response.version += 1
            response.status = ResponseStatus.DRAFT
        else:
            response = Response(
                analysis_id=analysis_id,
                generated_content=answers,
                status=ResponseStatus.DRAFT,
                version=1
            )
            db.add(response)
        db.commit()
        db.refresh(response)
        return response

    @staticmethod
    def regenerate_single_question(analysis_id: int, question_index: int, db: Session) -> str:
        analysis = db.query(RFPAnalysis).filter(RFPAnalysis.id == analysis_id).first()
        if not analysis or not analysis.extracted_requirements:
            raise ValueError("التحليل غير موجود")
        questions = analysis.extracted_requirements.get("technical_questions", [])
        if question_index < 0 or question_index >= len(questions):
            raise ValueError("رقم السؤال غير صحيح")
        q_text = questions[question_index].get("question", "")
        new_answer = ResponseGenerator._generate_single_answer(q_text, db, analysis.company_id)

        response = db.query(Response).filter(Response.analysis_id == analysis_id).first()
        if response and response.generated_content:
            answers = response.generated_content
            if isinstance(answers, list) and question_index < len(answers):
                answers[question_index]["answer"] = new_answer
                response.generated_content = answers
            db.commit()
        return new_answer