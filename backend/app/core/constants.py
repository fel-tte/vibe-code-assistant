"""
Global constants for the Render Factory application.

Centralises all magic numbers and configuration limits to avoid
hard-coded values scattered throughout the codebase.
"""
from __future__ import annotations

# ── Scene / job limits ───────────────────────────────────────────────────────
MAX_SCENES_PER_JOB: int = 50
MAX_SCENE_DURATION_SECONDS: int = 120
MIN_SCENE_DURATION_SECONDS: int = 1

# ── File / upload limits ─────────────────────────────────────────────────────
MAX_FILE_UPLOAD_SIZE_MB: int = 100
MAX_FILE_UPLOAD_SIZE_BYTES: int = MAX_FILE_UPLOAD_SIZE_MB * 1024 * 1024

# ── Video output defaults ────────────────────────────────────────────────────
DEFAULT_VIDEO_RESOLUTION: str = "1080p"
DEFAULT_ASPECT_RATIO: str = "16:9"
ALLOWED_ASPECT_RATIOS: frozenset[str] = frozenset({"16:9", "9:16", "1:1"})

# ── Provider / HTTP ──────────────────────────────────────────────────────────
PROVIDER_TIMEOUT_SECONDS: int = 120
MAX_RETRY_ATTEMPTS: int = 3
RETRY_BASE_SECONDS: int = 2
RETRY_MAX_SECONDS: int = 10

# ── Celery ───────────────────────────────────────────────────────────────────
DEFAULT_DISPATCH_BATCH_LIMIT: int = 10
DEFAULT_POLL_COUNTDOWN_SECONDS: int = 60
CELERY_TASK_TIME_LIMIT: int = 1800
CELERY_TASK_SOFT_TIME_LIMIT: int = 1500
CELERY_RESULT_EXPIRES_SECONDS: int = 86400  # 24 h

# ── Stuck-job recovery ───────────────────────────────────────────────────────
STUCK_JOB_THRESHOLD_SECONDS: int = 120
STUCK_JOB_MAX_RETRIES: int = 5

# ── Signed URL / storage ─────────────────────────────────────────────────────
DEFAULT_SIGNED_URL_EXPIRES_SECONDS: int = 3600

# ── Webhook security ─────────────────────────────────────────────────────────
WEBHOOK_SIGNATURE_TTL_SECONDS: int = 300
WEBHOOK_REPLAY_WINDOW_SECONDS: int = 300

# ── Rate limiting ────────────────────────────────────────────────────────────
RATE_LIMIT_CREATE_JOB: str = "10/minute"
RATE_LIMIT_DEFAULT: str = "60/minute"

# ── Logging ──────────────────────────────────────────────────────────────────
SENSITIVE_LOG_KEYS: frozenset[str] = frozenset(
    {"api_key", "secret", "password", "token", "access_key", "secret_key"}
)
