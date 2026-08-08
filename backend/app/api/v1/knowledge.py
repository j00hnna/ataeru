"""
نقاط نهاية API لقاعدة المعرفة.
"""
import os
import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.knowledge_document import KnowledgeDocument, DocumentStatus
from app.services.document_processor import DocumentProcessor
from app.services.embedding_service import EmbeddingService
from app.schemas.knowledge import KnowledgeDocumentOut

router = APIRouter(prefix="/knowledge", tags=["قاعدة المعرفة"])
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/upload", response_model=KnowledgeDocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    allowed = {"pdf", "docx", "doc", "png", "jpg", "jpeg"}
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed:
        raise HTTPException(400, "نوع ملف غير مدعوم")
    file_name = f"{current_user.company_id}_{current_user.id}_{file.filename}"
    file_path = UPLOAD_DIR / file_name
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    doc = KnowledgeDocument(
        company_id=current_user.company_id,
        file_name=file.filename,
        file_url=str(file_path.resolve()),
        file_type=ext.upper() if ext not in ["png","jpg","jpeg"] else "IMAGE",
        status=DocumentStatus.UPLOADED
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # معالجة غير متزامنة بسيطة
    try:
        DocumentProcessor.process_uploaded_file(doc, db)
        EmbeddingService.embed_all_document_chunks(doc.id, db)
        db.refresh(doc)
    except Exception:
        doc.status = DocumentStatus.FAILED
        db.commit()
    return doc

@router.get("/documents", response_model=List[KnowledgeDocumentOut])
def list_documents(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(KnowledgeDocument).filter(KnowledgeDocument.company_id == current_user.company_id).order_by(KnowledgeDocument.uploaded_at.desc()).all()

@router.get("/search")
def search_knowledge(query: str, top_k: int = 5, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chunks = EmbeddingService.search_similar_chunks(query, db, current_user.company_id, top_k)
    return {"results": [{"chunk_id": c.id, "text": c.chunk_text} for c in chunks]}