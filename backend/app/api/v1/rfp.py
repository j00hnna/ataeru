"""
نقاط نهاية API لتحليل العطاءات (غير متزامنة عبر Celery + Redis caching).
"""
import os
import uuid
import logging
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.cache import cache_service
from app.api.deps import get_current_user
from app.models.user import User
from app.models.rfp_analysis import RFPAnalysis, AnalysisStatus
from app.schemas.rfp import RFPAnalysisOut, RFPAnalysisUpdate
from celery_app import process_rfp_analysis

logger = logging.getLogger("ataeru.rfp")
router = APIRouter(prefix="/rfp", tags=["تحليل العطاءات"])

ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "xlsx", "xls", "txt"}

UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_rfp(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    رفع ملف عطاء وبدء تحليله في الخلفية (غير متزامن).
    """
    file_extension = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ""
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"نوع الملف غير مسموح. المسموح: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    file_size = await file.read()
    if len(file_size) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"حجم الملف يتجاوز {settings.MAX_FILE_SIZE // (1024 * 1024)}MB"
        )

    # حفظ الملف
    file_id = uuid.uuid4().hex
    safe_name = f"{file_id}_{file.filename}"
    file_path = UPLOAD_DIR / safe_name
    file_path.write_bytes(file_size)

    # إنشاء سجل التحليل
    analysis = RFPAnalysis(
        user_id=current_user.id,
        company_id=current_user.company_id,
        original_file_name=file.filename,
        original_file_url=str(file_path.resolve()),
        status=AnalysisStatus.QUEUED,
        progress=0,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    logger.info(f"File uploaded: analysis {analysis.id}, path: {file_path}")

    # إرسال للـ queue
    task = process_rfp_analysis.delay(analysis.id)
    analysis.celery_task_id = task.id
    db.commit()

    logger.info(f"Task {task.id} queued for analysis {analysis.id}")

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "analysis_id": analysis.id,
            "task_id": task.id,
            "status": AnalysisStatus.QUEUED.value,
            "message": "جارٍ معالجة الملف، يمكنك متابعة التقدم من خلال /status",
            "check_status_url": f"/api/v1/rfp/status/{analysis.id}",
        },
    )


@router.get("/status/{analysis_id}")
def get_analysis_status(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """التحقق من حالة التحليل."""
    analysis = db.query(RFPAnalysis).filter(
        RFPAnalysis.id == analysis_id,
        RFPAnalysis.company_id == current_user.company_id,
    ).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="التحليل غير موجود")

    return {
        "id": analysis.id,
        "status": analysis.status.value if hasattr(analysis.status, "value") else analysis.status,
        "quality_score": analysis.quality_score,
        "confidence_score": analysis.confidence_score,
        "progress": analysis.progress,
        "retry_count": analysis.retry_count,
        "attempt": analysis.current_attempt,
        "completed_at": analysis.completed_at,
        "error_message": analysis.error_message if analysis.status == AnalysisStatus.FAILED else None,
        "result": analysis.analysis_result if analysis.status == AnalysisStatus.COMPLETED else None,
    }


@router.get("/list")
def list_analyses(
    status_filter: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """قائمة بجميع التحليلات مع فلترة وصفحات."""
    query = db.query(RFPAnalysis).filter(
        RFPAnalysis.company_id == current_user.company_id
    )

    if status_filter:
        query = query.filter(RFPAnalysis.status == status_filter)

    total = query.count()
    analyses = query.order_by(RFPAnalysis.created_at.desc()).limit(limit).offset(offset).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "analyses": [
            {
                "id": a.id,
                "filename": a.original_file_name,
                "status": a.status.value if hasattr(a.status, "value") else a.status,
                "quality_score": a.quality_score,
                "confidence_score": a.confidence_score,
                "created_at": a.created_at,
                "completed_at": a.completed_at,
            }
            for a in analyses
        ],
    }


@router.get("/analyses", response_model=List[RFPAnalysisOut])
def list_analyses_compat(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    عرض قائمة بتحليلات العطاءات الخاصة بالشركة الحالية (متوافق مع النسخة السابقة).
    """
    analyses = db.query(RFPAnalysis).filter(
        RFPAnalysis.company_id == current_user.company_id
    ).order_by(RFPAnalysis.created_at.desc()).all()
    return analyses


@router.get("/{analysis_id}", response_model=RFPAnalysisOut)
def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    عرض تفاصيل تحليل عطاء محدد مع caching للنتائج المكتملة.
    """
    cache_key = f"analysis:{analysis_id}:company:{current_user.company_id}"

    analysis = db.query(RFPAnalysis).filter(
        RFPAnalysis.id == analysis_id,
        RFPAnalysis.company_id == current_user.company_id,
    ).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="التحليل غير موجود")

    # cache النتائج المكتملة فقط (الحالات قيد المعالجة تُقرأ حية)
    if analysis.status == AnalysisStatus.COMPLETED:
        cached = cache_service.get_sync(cache_key)
        if cached:
            logger.info(f"Returning cached analysis {analysis_id}")
            return cached

        result = {
            "id": analysis.id,
            "company_id": analysis.company_id,
            "user_id": analysis.user_id,
            "original_file_name": analysis.original_file_name,
            "original_file_url": analysis.original_file_url,
            "status": analysis.status.value if hasattr(analysis.status, "value") else analysis.status,
            "quality_score": analysis.quality_score,
            "confidence_score": analysis.confidence_score,
            "extracted_requirements": analysis.extracted_requirements,
            "mandatory_checklist": analysis.mandatory_checklist,
            "evaluation_criteria": analysis.evaluation_criteria,
            "error_message": analysis.error_message,
            "created_at": analysis.created_at,
            "updated_at": analysis.updated_at,
        }

        cache_service.set_sync(cache_key, result)

        return result

    return analysis


@router.put("/{analysis_id}", response_model=RFPAnalysisOut)
def update_analysis(
    analysis_id: int,
    update_data: RFPAnalysisUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    تعديل بيانات التحليل (مثل المتطلبات المستخرجة يدوياً).
    """
    analysis = db.query(RFPAnalysis).filter(
        RFPAnalysis.id == analysis_id,
        RFPAnalysis.company_id == current_user.company_id,
    ).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="التحليل غير موجود")

    if update_data.extracted_requirements is not None:
        analysis.extracted_requirements = update_data.extracted_requirements
        analysis.analysis_result = update_data.extracted_requirements
    if update_data.mandatory_checklist is not None:
        analysis.mandatory_checklist = update_data.mandatory_checklist
    if update_data.evaluation_criteria is not None:
        analysis.evaluation_criteria = update_data.evaluation_criteria

    analysis.is_validated = True
    db.commit()
    db.refresh(analysis)

    # إبطال الـ cache بعد التعديل
    cache_service.delete_sync(f"analysis:{analysis_id}:company:{current_user.company_id}")

    return analysis
