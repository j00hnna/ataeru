"""
إعداد Celery: المعالجة غير المتزامنة للتحليلات والتصدير.
"""
import asyncio
import logging

from celery import Celery
from kombu import Exchange, Queue

from app.core.config import settings

logger = logging.getLogger("ataeru.celery")

celery_app = Celery(
    "ataeru",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=60 * 5,      # 5 minutes hard limit
    task_soft_time_limit=60 * 4, # 4 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Define task queues
default_exchange = Exchange("ataeru", type="direct")

celery_app.conf.task_queues = (
    Queue("default", default_exchange, routing_key="default"),
    Queue("analysis", default_exchange, routing_key="analysis.process"),
    Queue("exports", default_exchange, routing_key="exports.generate"),
)

# Routes
celery_app.conf.task_routes = {
    "celery_app.process_rfp_analysis": {"queue": "analysis"},
    "celery_app.generate_export": {"queue": "exports"},
}


@celery_app.task(
    bind=True,
    max_retries=3,
    queue="analysis",
    name="celery_app.process_rfp_analysis",
)
def process_rfp_analysis(self, analysis_id: int):
    """معالجة RFP في الخلفية بشكل غير متزامن."""
    from sqlalchemy.orm import Session
    from app.core.database import SessionLocal
    from app.services.robust_rfp_service import RobustRFPService

    db: Session = SessionLocal()
    try:
        logger.info(f"Task started for analysis {analysis_id}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                RobustRFPService.extract_and_analyze_robust(db, analysis_id)
            )
        finally:
            loop.close()

        logger.info(f"Task completed for analysis {analysis_id}: success={result.get('success')}")
        return result

    except Exception as exc:
        logger.error(f"Task failed for analysis {analysis_id}: {str(exc)}", exc_info=True)

        try:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for analysis {analysis_id}")
            raise

    finally:
        db.close()


@celery_app.task(
    bind=True,
    queue="exports",
    name="celery_app.generate_export",
)
def generate_export(self, analysis_id: int, format: str = "pdf"):
    """توليد تقرير التصدير."""
    logger.info(f"Generating {format} export for analysis {analysis_id}")
