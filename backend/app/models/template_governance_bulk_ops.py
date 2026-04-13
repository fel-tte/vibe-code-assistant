"""
SQLAlchemy ORM models for template governance bulk operations analytics.

These models correspond to the tables created in Alembic migration
20260412_0025_governance_execution_backfill.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Float, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TemplateGovernanceActionOutcomeAnalytics(Base):
    """Records the outcome of a single governance action within a bulk operation."""

    __tablename__ = "template_governance_action_outcome_analytics"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    bulk_operation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    plan_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    target_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    action_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    outcome_label: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    impact_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True
    )
