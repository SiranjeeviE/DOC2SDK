import asyncio
import logging
import os
from uuid import UUID
from celery import Celery

logger = logging.getLogger("doc2sdk.celery")

# Redis configuration from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize single Celery application
celery_app = Celery(
    "doc2sdk",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

# Standard aliases for Celery CLI discovery (e.g. `celery -A tasks worker`)
app = celery_app
celery = celery_app


@celery_app.task(name="process_project_task")
def process_project_task(project_id_str: str, source_url: str) -> bool:
    """
    Celery background task to scrape documentation, parse OpenAPI spec,
    and generate SDK for a project asynchronously.
    """
    logger.info("Executing Celery background task for project %s (URL: %s)", project_id_str, source_url)
    try:
        from app.routers.projects import process_project_background
        project_uuid = UUID(project_id_str)
        asyncio.run(process_project_background(project_uuid, source_url))
        logger.info("Celery task finished successfully for project %s", project_id_str)
        return True
    except Exception as e:
        logger.exception("Celery task failed for project %s: %s", project_id_str, e)
        return False


@celery_app.task(name="monitor_api_changes_task")
def monitor_api_changes_task(project_id_str: str) -> bool:
    """
    Celery background task to detect breaking/non-breaking changes in external API specs.
    """
    logger.info("Executing API change monitor task for project %s", project_id_str)
    try:
        from app.routers.projects import check_api_changes_background
        project_uuid = UUID(project_id_str)
        asyncio.run(check_api_changes_background(project_uuid))
        logger.info("Change monitoring task finished successfully for project %s", project_id_str)
        return True
    except Exception as e:
        logger.exception("Change monitoring task failed for project %s: %s", project_id_str, e)
        return False

