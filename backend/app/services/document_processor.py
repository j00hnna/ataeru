"""
خدمة معالجة المستندات: استخراج النص، تقسيم إلى أجزاء، وحفظ التضمينات.
"""
import os
from pathlib import Path
from typing import List
import pdfplumber
import PyPDF2
from docx import Document as DocxDocument
from sqlalchemy.orm import Session
from app.models.knowledge_document import KnowledgeDocument, DocumentStatus
from app.models.document_chunk import DocumentChunk
from langchain_text_splitters import RecursiveCharacterTextSplitter

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

class DocumentProcessor:
    @staticmethod
    def extract_text(file_path: str, file_type: str) -> str:
        if file_type.upper() == "PDF":
            return DocumentProcessor._extract_text_from_pdf(file_path)
        elif file_type.upper() in ["DOCX", "DOC"]:
            return DocumentProcessor._extract_text_from_docx(file_path)
        else:
            raise ValueError(f"نوع ملف غير مدعوم: {file_type}")

    @staticmethod
    def _extract_text_from_pdf(file_path: str) -> str:
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception:
            pass
        if not text.strip():
            try:
                with open(file_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception:
                pass
        return text.strip()

    @staticmethod
    def _extract_text_from_docx(file_path: str) -> str:
        doc = DocxDocument(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text.strip()

    @staticmethod
    def chunk_text(text: str) -> List[str]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        return splitter.split_text(text)

    @staticmethod
    def process_uploaded_file(document: KnowledgeDocument, db: Session):
        try:
            document.status = DocumentStatus.PROCESSING
            db.commit()
            text = DocumentProcessor.extract_text(document.file_url, document.file_type)
            if not text:
                raise ValueError("لم يتم استخراج أي نص من الملف")
            chunks = DocumentProcessor.chunk_text(text)
            for i, chunk_text in enumerate(chunks):
                chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_text=chunk_text,
                    chunk_index=i
                )
                db.add(chunk)
            document.chunk_count = len(chunks)
            document.status = DocumentStatus.READY
            db.commit()
        except Exception as e:
            document.status = DocumentStatus.FAILED
            db.commit()
            raise e