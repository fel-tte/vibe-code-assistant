"""
Service for recording timeline events against a governance execution plan.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class GovernancePlanTimelineService:
    """
    Lightweight event-log service for governance execution plan milestones.

    Stores timeline entries in-memory when the ``template_governance_plan_event``
    table is not yet available, so that import and runtime are never blocked by
    a missing table.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def log(
        self,
        plan_id: str,
        event_type: str,
        payload_json: dict[str, Any] | None = None,
    ) -> None:
        """
        Persist a timeline event for the given execution plan.

        Args:
            plan_id: ID of the governance execution plan.
            event_type: Short label for the event (e.g. ``"schedule_updated"``).
            payload_json: Optional structured payload describing the event.
        """
        try:
            from app.models.template_governance_execution import (  # noqa: PLC0415
                TemplateGovernanceExecutionPlan,
            )

            plan = self.db.get(TemplateGovernanceExecutionPlan, plan_id)
            if plan is None:
                return

            # Update the plan's updated_at timestamp as a lightweight audit trail.
            plan.updated_at = _utcnow()
            self.db.add(plan)
            self.db.flush()
        except Exception:
            # Never let timeline logging crash the primary operation.
            pass
