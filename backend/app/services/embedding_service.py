"""
خدمة التضمين والبحث الدلالي.
"""
import json
import logging
import numpy as np
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.document_chunk import DocumentChunk

logger = logging.getLogger("ataeru.embeddings")

class EmbeddingService:
    _model: Optional[object] = None
    _load_error: Optional[str] = None

    @classmethod
    def get_model(cls):
        # تحميل Lazy حتى لا يتطلب torch وقت تشغيل التطبيق
        if cls._load_error:
            raise RuntimeError(cls._load_error)
        if cls._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                cls._model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            except Exception as e:
                cls._load_error = f"تعذر تحميل نموذج التضمين: {e}"
                logger.warning(cls._load_error)
                raise RuntimeError(cls._load_error)
        return cls._model

    @classmethod
    def create_embedding(cls, text: str) -> List[float]:
        model = cls.get_model()
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    @classmethod
    def embed_chunk(cls, chunk: DocumentChunk, db: Session):
        if chunk.embedding_json:
            return
        embedding = cls.create_embedding(chunk.chunk_text)
        chunk.embedding_json = json.dumps(embedding)
        db.commit()

    @classmethod
    def embed_all_document_chunks(cls, document_id: int, db: Session):
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id,
            DocumentChunk.embedding_json == None
        ).all()
        for chunk in chunks:
            cls.embed_chunk(chunk, db)

    @classmethod
    def search_similar_chunks(
        cls,
        query: str,
        db: Session,
        company_id: int,
        top_k: int = 5
    ) -> List[DocumentChunk]:
        try:
            query_embedding = cls.create_embedding(query)
        except Exception as e:
            logger.warning(f"البحث الدلالي غير متاح (لا يوجد نموذج تضمين): {e}")
            return []
        query_vector = np.array(query_embedding)

        chunks = db.query(DocumentChunk).join(
            DocumentChunk.document
        ).filter(
            DocumentChunk.embedding_json.isnot(None),
            DocumentChunk.document.has(company_id=company_id)
        ).all()

        if not chunks:
            return []

        similarities = []
        for chunk in chunks:
            try:
                emb = np.array(json.loads(chunk.embedding_json))
                sim = np.dot(query_vector, emb)  # cosine similarity because normalized
                similarities.append((chunk, sim))
            except Exception:
                continue

        similarities.sort(key=lambda x: x[1], reverse=True)
        return [chunk for chunk, _ in similarities[:top_k]]