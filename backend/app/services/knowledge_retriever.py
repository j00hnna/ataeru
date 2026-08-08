"""
خدمة استرجاع المعرفة: تجميع السياق من الوثائق والمشاريع السابقة لاستخدامه في RAG.
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.services.embedding_service import EmbeddingService
from app.models.document_chunk import DocumentChunk

class KnowledgeRetriever:
    @staticmethod
    def get_context_for_query(
        query: str,
        db: Session,
        company_id: int,
        top_k: int = 5
    ) -> str:
        """
        استرجاع أفضل الأجزاء المطابقة من قاعدة المعرفة، وإرجاع نص موحد.
        """
        chunks = EmbeddingService.search_similar_chunks(
            query=query,
            db=db,
            company_id=company_id,
            top_k=top_k
        )
        if not chunks:
            return "لا توجد معلومات سابقة ذات صلة."
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(f"[مقتطف {i}]: {chunk.chunk_text}")
        return "\n\n".join(context_parts)