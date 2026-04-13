"""
Unit tests for backend/app/core/constants.py
"""
from __future__ import annotations

import pytest

from app.core.constants import (
    ALLOWED_ASPECT_RATIOS,
    CELERY_RESULT_EXPIRES_SECONDS,
    CELERY_TASK_TIME_LIMIT,
    MAX_FILE_UPLOAD_SIZE_BYTES,
    MAX_FILE_UPLOAD_SIZE_MB,
    MAX_RETRY_ATTEMPTS,
    MAX_SCENES_PER_JOB,
    PROVIDER_TIMEOUT_SECONDS,
    RATE_LIMIT_CREATE_JOB,
    SENSITIVE_LOG_KEYS,
    WEBHOOK_SIGNATURE_TTL_SECONDS,
)


def test_max_scenes_is_positive() -> None:
    assert MAX_SCENES_PER_JOB > 0


def test_file_upload_size_consistency() -> None:
    assert MAX_FILE_UPLOAD_SIZE_BYTES == MAX_FILE_UPLOAD_SIZE_MB * 1024 * 1024


def test_allowed_aspect_ratios_are_non_empty() -> None:
    assert len(ALLOWED_ASPECT_RATIOS) > 0
    assert "16:9" in ALLOWED_ASPECT_RATIOS


def test_provider_timeout_positive() -> None:
    assert PROVIDER_TIMEOUT_SECONDS > 0


def test_max_retry_attempts_positive() -> None:
    assert MAX_RETRY_ATTEMPTS > 0


def test_celery_result_expires_positive() -> None:
    assert CELERY_RESULT_EXPIRES_SECONDS > 0


def test_celery_task_time_limit_greater_than_provider_timeout() -> None:
    assert CELERY_TASK_TIME_LIMIT > PROVIDER_TIMEOUT_SECONDS


def test_sensitive_log_keys_contain_expected_keys() -> None:
    assert "api_key" in SENSITIVE_LOG_KEYS
    assert "password" in SENSITIVE_LOG_KEYS
    assert "token" in SENSITIVE_LOG_KEYS


def test_rate_limit_format_is_valid() -> None:
    """Rate limit strings should follow '<count>/<period>' format."""
    parts = RATE_LIMIT_CREATE_JOB.split("/")
    assert len(parts) == 2
    count, period = parts
    assert int(count) > 0
    assert period in {"second", "minute", "hour", "day"}


def test_webhook_signature_ttl_positive() -> None:
    assert WEBHOOK_SIGNATURE_TTL_SECONDS > 0
