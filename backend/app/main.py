"""
تطبيق Ataeru الرئيسي.
"""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.core.config import settings
from app.api.v1.router import api_v1_router
from app.core.database import engine, Base
from app.core.logging_config import setup_logging

setup_logging()
logger = logging.getLogger("ataeru")

# استيراد جميع النماذج لإنشاء الجداول
import app.models.user
import app.models.company
import app.models.rfp_analysis
import app.models.response
import app.models.knowledge_document
import app.models.document_chunk

Base.metadata.create_all(bind=engine)

limiter = Limiter(key_func=get_remote_address)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        if request.url.path.startswith("/docs") or request.url.path.startswith("/redoc"):
            csp = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'"
        else:
            csp = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
        response.headers["Content-Security-Policy"] = csp
        return response

app = FastAPI(title="Ataeru API", version="1.0.0", docs_url="/docs", redoc_url="/redoc")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda req, exc: JSONResponse(status_code=429, content={"detail": "طلبات كثيرة جداً"}))

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(CORSMiddleware, allow_origins=[str(o) for o in settings.BACKEND_CORS_ORIGINS], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(SlowAPIMiddleware)
app.include_router(api_v1_router, prefix="/api")

@app.get("/")
@limiter.limit("5/minute")
async def root(request: Request):
    return {"message": "Ataeru API", "docs": "/docs"}

@app.get("/health")
@limiter.limit("10/minute")
async def health(request: Request):
    return {"status": "healthy"}