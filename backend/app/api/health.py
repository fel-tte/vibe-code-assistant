from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.services.healthcheck_service import (
    build_full_health_payload,
    check_database,
    check_object_storage,
    check_redis,
    check_worker_runtime,
    summarize_health,
)
from app.services.render_fsm import describe_fsm, get_transition_metrics_snapshot

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict:
    """
    Aggregate health endpoint for the entire backend runtime.
    """
    checks = [
        check_database(),
        check_redis(),
        check_object_storage(),
        check_worker_runtime(),
    ]
    return summarize_health(checks)


@router.get("/healthz/detailed")
async def healthz_detailed() -> JSONResponse:
    """
    Detailed health check that returns 200 when all subsystems are healthy
    and 503 when any subsystem is degraded.
    """
    payload = build_full_health_payload()
    status_code = 200 if payload.get("ok") else 503
    return JSONResponse(content=payload, status_code=status_code)


@router.get("/healthz/postgres")
async def healthz_postgres() -> dict:
    """
    Health check for Postgres.
    """
    return check_database()


@router.get("/healthz/redis")
async def healthz_redis() -> dict:
    """
    Health check for Redis/Celery broker.
    """
    return check_redis()


@router.get("/healthz/object-storage")
async def healthz_object_storage() -> dict:
    """
    Health check for MinIO/S3-compatible object storage.
    """
    return check_object_storage()


@router.get("/healthz/workers")
async def healthz_workers() -> dict:
    """
    Basic health check for the Celery worker runtime.
    """
    return check_worker_runtime()


@router.get("/healthz/fsm")
async def healthz_fsm() -> dict:
    """
    Expose FSM metrics + transition map for orchestration debugging.
    """
    return {
        "ok": True,
        "metrics": get_transition_metrics_snapshot(),
        "fsm": describe_fsm(),
    }
