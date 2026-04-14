"""
Unit tests for backend/app/core/logging_utils.py
"""
from __future__ import annotations

import pytest

from app.core.logging_utils import sanitize_for_logging


def test_non_sensitive_keys_are_unchanged() -> None:
    data = {"user_id": "abc123", "status": "ok", "count": 5}
    result = sanitize_for_logging(data)
    assert result == data


def test_sensitive_api_key_is_redacted() -> None:
    data = {"api_key": "sk-supersecret"}
    result = sanitize_for_logging(data)
    assert result["api_key"] == "***REDACTED***"


def test_sensitive_password_is_redacted() -> None:
    data = {"password": "hunter2", "username": "alice"}
    result = sanitize_for_logging(data)
    assert result["password"] == "***REDACTED***"
    assert result["username"] == "alice"


def test_sensitive_token_is_redacted() -> None:
    data = {"access_token": "Bearer xyz"}
    result = sanitize_for_logging(data)
    assert result["access_token"] == "***REDACTED***"


def test_nested_dict_is_sanitized() -> None:
    data = {"config": {"secret": "top-secret", "level": 3}}
    result = sanitize_for_logging(data)
    assert result["config"]["secret"] == "***REDACTED***"
    assert result["config"]["level"] == 3


def test_original_dict_is_not_mutated() -> None:
    original = {"api_key": "should-not-change"}
    sanitize_for_logging(original)
    assert original["api_key"] == "should-not-change"


def test_empty_dict_returns_empty_dict() -> None:
    assert sanitize_for_logging({}) == {}


def test_key_with_mixed_case_is_redacted() -> None:
    data = {"API_KEY": "value", "Secret_Token": "value2"}
    result = sanitize_for_logging(data)
    assert result["API_KEY"] == "***REDACTED***"
    assert result["Secret_Token"] == "***REDACTED***"
