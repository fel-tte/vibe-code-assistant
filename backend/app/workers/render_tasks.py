from __future__ import annotations

import asyncio
import logging

from celery.exceptions import SoftTimeLimitExceeded

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.workers.render_dispatch_worker import process_render_dispatch
from app.workers.render_poll_worker import process_render_poll
from app.workers.render_postprocess_worker import process_render_postprocess

logger = logging.getLogger(__name__)


@celery_app.task(
    name="render.dispatch",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
)
def render_dispatch_task(self, job_id: str) -> None:
    """Dispatch a render job to the configured video provider."""
    db = SessionLocal()
    try:
        asyncio.run(process_render_dispatch(db, job_id))
    except SoftTimeLimitExceeded:
        logger.error("render.dispatch soft time limit exceeded for job_id=%s", job_id)
        raise
    except Exception as exc:
        logger.error("render.dispatch failed for job_id=%s: %s", job_id, exc, exc_info=True)
        raise
    finally:
        db.close()


@celery_app.task(
    name="render.poll",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
)
def render_poll_task(self, job_id: str, scene_task_id: str) -> None:
    """Poll provider for the status of a submitted scene task."""
    db = SessionLocal()
    try:
        asyncio.run(process_render_poll(db, job_id, scene_task_id))
    except SoftTimeLimitExceeded:
        logger.error(
            "render.poll soft time limit exceeded for job_id=%s scene_id=%s",
            job_id,
            scene_task_id,
        )
        raise
    except Exception as exc:
        logger.error(
            "render.poll failed for job_id=%s scene_id=%s: %s",
            job_id,
            scene_task_id,
            exc,
            exc_info=True,
        )
        raise
    finally:
        db.close()


@celery_app.task(
    name="render.postprocess",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
)
def render_postprocess_task(self, job_id: str) -> None:
    """Run post-processing (merge, subtitle burn) for a completed render job."""
    db = SessionLocal()
    try:
        asyncio.run(process_render_postprocess(db, job_id))
    except SoftTimeLimitExceeded:
        logger.error("render.postprocess soft time limit exceeded for job_id=%s", job_id)
        raise
    except Exception as exc:
        logger.error("render.postprocess failed for job_id=%s: %s", job_id, exc, exc_info=True)
        raise
    finally:
        db.close()
