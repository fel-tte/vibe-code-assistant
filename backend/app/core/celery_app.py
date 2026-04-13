from __future__ import annotations

from celery import Celery
from celery.schedules import crontab  # noqa: F401 – kept for beat schedule definitions

from app.core.config import settings
from app.core.constants import CELERY_RESULT_EXPIRES_SECONDS


celery_app = Celery(
    "render_factory",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.workers.render_tasks",
        "app.workers.stuck_job_recovery_worker",
        "app.workers.template_analytics_worker",
        "app.workers.template_batch_worker",
        "app.workers.template_generation_worker",
        "app.workers.template_extraction_worker",
        "app.workers.template_rescore_worker",
        "app.workers.template_feedback_worker",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_acks_late=settings.celery_task_acks_late,
    worker_prefetch_multiplier=settings.celery_worker_prefetch_multiplier,
    task_time_limit=settings.celery_task_time_limit,
    task_soft_time_limit=settings.celery_task_soft_time_limit,
    worker_send_task_events=True,
    task_send_sent_event=True,
    timezone="UTC",
    enable_utc=True,
    # Expire results after 24 h to avoid Redis memory pressure
    result_expires=CELERY_RESULT_EXPIRES_SECONDS,
    # Task routing – keeps queues focused and avoids noisy-neighbour effects
    task_routes={
        "render.dispatch": {"queue": "dispatch"},
        "render.poll": {"queue": "poll"},
        "render.postprocess": {"queue": "postprocess"},
        "render.recover_stuck": {"queue": "dispatch"},
        "app.workers.template_*": {"queue": "templates"},
    },
    # Limit how many unacknowledged tasks a worker can hold at once
    # (already set above via worker_prefetch_multiplier)
)

celery_app.conf.beat_schedule = {
    "recover-stuck-render-tasks": {
        "task": "render.recover_stuck",
        "schedule": 120.0,
    },
    "autopilot-evaluate-control-fabric-every-5-minutes": {
        "task": "autopilot.evaluate_control_fabric",
        "schedule": 300.0,
    },
}
