"""
خدمة استرجاع المعرفة (RAG) للردود.
"""
from sqlalchemy.orm import Session
from app.services.embedding_service import EmbeddingService

class RAGService:
    @staticmethod
    def retrieve_context(query: str, db: Session, company_id: int, top_k: int = 5) -> str:
        chunks = EmbeddingService.search_similar_chunks(query, db, company_id, top_k)
        if not chunks:
            return "لا توجد معلومات سابقة ذات صلة."
        return "\n\n".join([f"[مقتطف {i+1}]: {chunk.chunk_text}" for i, chunk in enumerate(chunks)])