from fastapi import APIRouter
from .auth import router as auth_router
from .knowledge import router as knowledge_router
from .rfp import router as rfp_router
from .responses import router as responses_router
from .billing import router as billing_router
from .admin import router as admin_router
from .analytics import router as analytics_router

api_v1_router = APIRouter(prefix="/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(knowledge_router)
api_v1_router.include_router(rfp_router)
api_v1_router.include_router(responses_router)
api_v1_router.include_router(billing_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(analytics_router)