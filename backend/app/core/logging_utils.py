"""
Logging utilities for the Render Factory application.

Provides helpers that prevent sensitive credential data from leaking
into log output.
"""
from __future__ import annotations

from typing import Any

from app.core.constants import SENSITIVE_LOG_KEYS


def sanitize_for_logging(data: dict[str, Any]) -> dict[str, Any]:
    """
    Return a copy of *data* with values for known-sensitive keys replaced
    by ``'***REDACTED***'``.

    The check is case-insensitive and handles nested dict values
    one level deep.

    Args:
        data: Arbitrary dict (e.g. a request payload or config snapshot).

    Returns:
        Sanitised shallow copy of *data*.
    """
    result: dict[str, Any] = {}
    for key, value in data.items():
        lower_key = key.lower()
        if any(sensitive in lower_key for sensitive in SENSITIVE_LOG_KEYS):
            result[key] = "***REDACTED***"
        elif isinstance(value, dict):
            result[key] = sanitize_for_logging(value)
        else:
            result[key] = value
    return result
