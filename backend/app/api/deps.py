"""
Common FastAPI dependency helpers used across API route modules.
"""
from __future__ import annotations

from app.db.session import get_db  # re-export for convenience

__all__ = ["get_db"]
