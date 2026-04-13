# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] – 2026-04-13

### 🐛 Critical Bug Fixes
- **`backend/app/workers/template_extraction_worker.py`** – Fixed `IndentationError` on line 13 that caused the CI compilation step to fail. The `result = TemplateExtractionService(repo).perform_extraction(extraction_id)` line was incorrectly indented inside the early-return `if` block.
- **`backend/app/api/templates.py`** – Fixed two `IndentationError` occurrences (lines 25 and 45) where `return` statements inside `extract_template()` and `create_template()` had an extra level of indentation, causing the entire module to fail compilation.

### 🔒 Security Hardening
- **`backend/app/main.py`** – Added `RequestIDMiddleware` that attaches a unique `X-Request-ID` header to every request and response, enabling full distributed tracing.
- **`backend/app/main.py`** – Integrated `slowapi` rate-limiter (gracefully skipped when package not installed). The `app.state.limiter` and `RateLimitExceeded` handler are registered at startup.
- **`backend/app/core/logging_utils.py`** *(new)* – `sanitize_for_logging()` helper that redacts known-sensitive keys (`api_key`, `secret`, `password`, `token`, `access_key`, `secret_key`) from log payloads to prevent credential leakage.

### 🚀 Performance Optimisation
- **`backend/alembic/versions/20260413_0026_add_performance_indexes.py`** *(new)* – Alembic migration that adds composite indexes on `render_jobs(status)`, `render_jobs(created_at)`, `render_jobs(project_id, status)`, `render_scene_tasks(job_id)`, `render_scene_tasks(status)`, and `render_scene_tasks(job_id, status)` to eliminate full-table scans on hot query paths.
- **`backend/app/core/celery_app.py`** – Added `task_routes` to route `render.*` tasks to dedicated queues (`dispatch`, `poll`, `postprocess`) and template tasks to a `templates` queue. Added `result_expires` (24 h) to prevent unbounded Redis growth.

### 🛡️ Resilience & Worker Hardening
- **`backend/app/workers/render_tasks.py`** – All three Celery tasks (`render.dispatch`, `render.poll`, `render.postprocess`) now use `bind=True` with `autoretry_for=(Exception,)`, exponential back-off (`retry_backoff=True`, `retry_backoff_max=600 s`), jitter, and a `max_retries=3` cap. `SoftTimeLimitExceeded` is caught and re-raised for clean shutdown.

### 📊 Observability
- **`backend/app/api/health.py`** – Added `/healthz/detailed` endpoint that runs a full Postgres + Redis + Celery broker + workers check and returns HTTP 200 when all are healthy or HTTP 503 when any subsystem is degraded.

### 🏗️ Code Quality
- **`backend/app/core/constants.py`** *(new)* – Single source of truth for all magic numbers: `MAX_SCENES_PER_JOB`, `MAX_FILE_UPLOAD_SIZE_MB`, `PROVIDER_TIMEOUT_SECONDS`, `MAX_RETRY_ATTEMPTS`, `CELERY_RESULT_EXPIRES_SECONDS`, rate-limit strings, sensitive-key list, etc.

### 🧪 Testing
- **`backend/tests/test_constants.py`** *(new)* – Unit tests validating all public constants have sane values and correct relationships (e.g. `CELERY_TASK_TIME_LIMIT > PROVIDER_TIMEOUT_SECONDS`).
- **`backend/tests/test_logging_utils.py`** *(new)* – Unit tests for `sanitize_for_logging()` covering non-sensitive passthrough, multiple sensitive key names, nested dicts, mixed-case keys, and non-mutation of the original dict.

### 🖥️ Frontend
- **`frontend/src/components/ErrorBoundary.tsx`** *(new)* – React class component that catches unhandled render errors, logs them, and displays a user-friendly "Something went wrong / Try again" fallback with an accessible `role="alert"` container and `aria-label` on the retry button.

### 🐳 Infrastructure
- **`docker-compose.yml`** – Added `deploy.resources` limits/reservations for the `api` (2 CPU / 2 GB) and `worker` (2 CPU / 2 GB) services to prevent runaway memory usage.
- **`backend/.dockerignore`** – Extended to exclude `.git`, `.env.*` files (except `.env.example`), markdown files, and `seed_mock_job.py` from the Docker build context.
- **`frontend/.dockerignore`** – Extended to exclude `.git`, `.env.*` files, markdown files, and `Dockerfile` itself from the build context.

### 📦 Dependencies
- **`backend/requirements.txt`** – Added `slowapi` (rate limiting) and `tenacity` (retry helpers).

### 🔧 CI/CD
- **`.github/workflows/alembic-check.yml`** – Updated expected Alembic head from `20260412_9999` to `20260413_0026` following the new performance-indexes migration; also asserts `20260413_0026` is present in the revision graph.
