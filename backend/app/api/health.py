from __future__ import annotations

import logging

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

logger = logging.getLogger(__name__)

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


def _run_check(check_fn) -> bool:
    """
    Execute *check_fn* and return only a boolean status.

    Any exception raised by or message stored in the check result is logged
    server-side and is *never* forwarded to the HTTP response, preventing
    stack-trace / connection-string leakage (CWE-209).
    """
    try:
        result = check_fn()
        if isinstance(result, dict) and not result.get("ok"):
            logger.warning(
                "Health check degraded for %s",
                result.get("service", check_fn.__name__),
            )
            return False
        return bool(result.get("ok")) if isinstance(result, dict) else False
    except Exception:
        logger.exception("Health check raised an exception: %s", check_fn.__name__)
        return False


@router.get("/healthz/detailed")
async def healthz_detailed() -> JSONResponse:
    """
    Detailed health check – returns HTTP 200 when all subsystems are healthy
    and HTTP 503 when any subsystem is degraded.

    Only boolean ``ok`` flags are forwarded to the caller.  Detailed error
    strings are logged server-side only (CWE-209 / CodeQL py/stack-trace-exposure).
    """
    from app.services.healthcheck_service import (  # noqa: PLC0415
        check_celery_broker,
        check_celery_workers,
        check_postgres,
    )

    postgres_ok = _run_check(check_postgres)
    redis_ok = _run_check(check_redis)
    broker_ok = _run_check(check_celery_broker)
    workers_ok = _run_check(check_celery_workers)

    all_ok = postgres_ok and redis_ok and broker_ok and workers_ok

    payload: dict = {
        "ok": all_ok,
        "checks": {
            "postgres": {"ok": postgres_ok},
            "redis": {"ok": redis_ok},
            "celery_broker": {"ok": broker_ok},
            "celery_workers": {"ok": workers_ok},
        },
    }
    if not all_ok:
        payload["degraded"] = True

    return JSONResponse(content=payload, status_code=200 if all_ok else 503)


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
