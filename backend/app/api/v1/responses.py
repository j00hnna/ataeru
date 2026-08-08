"""
نقاط نهاية API لتوليد الردود، التصدير، والامتثال.
تتضمن استيراد ExportService.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.response import Response as ResponseModel, ResponseStatus
from app.models.rfp_analysis import RFPAnalysis
from app.services.response_generator import ResponseGenerator
from app.services.compliance_checker import ComplianceChecker
from app.services.export_service import ExportService
from app.schemas.response import ResponseOut

logger = logging.getLogger("ataeru")
router = APIRouter(prefix="/responses", tags=["الردود"])

def _handle_error(e, detail="حدث خطأ"):
    logger.error(e, exc_info=True)
    raise HTTPException(500, detail)

@router.post("/generate/{analysis_id}", response_model=ResponseOut)
def generate_response(analysis_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    analysis = db.query(RFPAnalysis).filter(RFPAnalysis.id == analysis_id, RFPAnalysis.company_id == current_user.company_id).first()
    if not analysis:
        raise HTTPException(404, "التحليل غير موجود")
    if analysis.status != "completed":
        raise HTTPException(400, "التحليل غير مكتمل")
    try:
        response = ResponseGenerator.generate_full_response(analysis_id, db)
        return response
    except Exception as e:
        _handle_error(e, "فشل توليد الرد")

@router.post("/regenerate/{analysis_id}/{question_index}", response_model=dict)
def regenerate_single(analysis_id: int, question_index: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    analysis = db.query(RFPAnalysis).filter(RFPAnalysis.id == analysis_id, RFPAnalysis.company_id == current_user.company_id).first()
    if not analysis:
        raise HTTPException(404, "التحليل غير موجود")
    try:
        new_answer = ResponseGenerator.regenerate_single_question(analysis_id, question_index, db)
        return {"question_index": question_index, "answer": new_answer}
    except Exception as e:
        _handle_error(e, "فشل إعادة التوليد")

@router.get("/{analysis_id}", response_model=ResponseOut)
def get_response(analysis_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    resp = db.query(ResponseModel).join(RFPAnalysis).filter(ResponseModel.analysis_id == analysis_id, RFPAnalysis.company_id == current_user.company_id).first()
    if not resp:
        raise HTTPException(404, "الرد غير موجود")
    return resp

@router.put("/{analysis_id}", response_model=ResponseOut)
def update_response(analysis_id: int, update: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    resp = db.query(ResponseModel).join(RFPAnalysis).filter(ResponseModel.analysis_id == analysis_id, RFPAnalysis.company_id == current_user.company_id).first()
    if not resp:
        raise HTTPException(404, "الرد غير موجود")
    if "answers" in update:
        resp.generated_content = update["answers"]
    elif "generated_content" in update:
        resp.generated_content = update["generated_content"]
    db.commit()
    db.refresh(resp)
    return resp

@router.post("/export/{analysis_id}")
def export_response(analysis_id: int, format: str = "docx", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    resp = db.query(ResponseModel).join(RFPAnalysis).filter(ResponseModel.analysis_id == analysis_id, RFPAnalysis.company_id == current_user.company_id).first()
    if not resp:
        raise HTTPException(404, "الرد غير موجود")
    if not resp.generated_content:
        raise HTTPException(400, "لا يوجد محتوى")
    if resp.compliance_score is not None and resp.compliance_score < 100.0:
        raise HTTPException(400, "يجب تحقيق امتثال 100% قبل التصدير")
    try:
        file_path = ExportService.export(resp, format)
        resp.final_document_url = str(file_path)
        resp.status = ResponseStatus.EXPORTED
        db.commit()
        return FileResponse(path=file_path, filename=f"response_{analysis_id}.{format}", media_type="application/octet-stream")
    except Exception as e:
        _handle_error(e, "فشل التصدير")

@router.post("/compliance/{analysis_id}", response_model=ResponseOut)
def run_compliance(analysis_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    analysis = db.query(RFPAnalysis).filter(RFPAnalysis.id == analysis_id, RFPAnalysis.company_id == current_user.company_id).first()
    if not analysis:
        raise HTTPException(404, "التحليل غير موجود")
    try:
        return ComplianceChecker.run_compliance_check(analysis_id, db)
    except Exception as e:
        _handle_error(e, "فشل فحص الامتثال")