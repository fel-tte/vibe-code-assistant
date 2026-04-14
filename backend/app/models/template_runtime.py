from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Optional
from sqlalchemy import Text, Integer, String, DateTime, ForeignKey, Numeric, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

def uuid_col():
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

class TemplateScore(Base):
    __tablename__ = "template_scores"
    id: Mapped[uuid.UUID] = uuid_col()
    template_pack_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("template_packs.id", ondelete="CASCADE"), nullable=False)
    render_score: Mapped[float] = mapped_column(Numeric(5,2), nullable=False, default=0)
    upload_score: Mapped[float] = mapped_column(Numeric(5,2), nullable=False, default=0)
    retention_score: Mapped[float] = mapped_column(Numeric(5,2), nullable=False, default=0)
    final_priority_score: Mapped[float] = mapped_column(Numeric(5,2), nullable=False, default=0)
    runs_considered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    snapshot_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    score_version: Mapped[str] = mapped_column(Text, nullable=False, default="v1")
    scoring_window: Mapped[str | None] = mapped_column(Text, nullable=True)
    weight_profile: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    score_details_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

class TemplateMemory(Base):
    __tablename__ = "template_memory"
    id: Mapped[uuid.UUID] = uuid_col()
    template_pack_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("template_packs.id", ondelete="CASCADE"), nullable=False, unique=True)
    state: Mapped[str] = mapped_column(Text, nullable=False, default="candidate")
    previous_state: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_score: Mapped[float | None] = mapped_column(Numeric(5,2), nullable=True)
    transition_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cooldown_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    promoted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    demoted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dominant_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stats_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

class TemplateSelectionDecision(Base):
    __tablename__ = "template_selection_decisions"
    id: Mapped[uuid.UUID] = uuid_col()
    template_pack_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("template_packs.id", ondelete="CASCADE"), nullable=False)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    decision_mode: Mapped[str] = mapped_column(Text, nullable=False, default="recommend")
    request_context_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    fit_score: Mapped[float] = mapped_column(Numeric(5,2), nullable=False, default=0)
    reason_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    alternatives_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    outcome_label: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


# ── Models added to fix pre-existing missing-model ImportErrors ──────────────
# These classes correspond to tables created in migration 20260412_0022
# but were never declared as SQLAlchemy ORM models.

class TemplateExtractionJob(Base):
    """Tracks a single template extraction attempt for a source project."""

    __tablename__ = "template_extraction_job"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_render_job_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued", index=True)
    source_project_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    output_template_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extraction_summary_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class TemplateExtractedDraft(Base):
    """A candidate template draft produced by an extraction job."""

    __tablename__ = "template_extracted_draft"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    extraction_job_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("template_extraction_job.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_render_job_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    scope_key: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    ratio: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    platform: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    scene_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_project_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    template_payload: Mapped[Any] = mapped_column(JSON, nullable=False, default=dict)
    preview_payload: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    tags_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class TemplateEvolutionEvent(Base):
    """Audit log of significant lifecycle events for a template pack."""

    __tablename__ = "template_evolution_event"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    template_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_project_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    source_render_job_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    payload_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class TemplateCompetitionRecord(Base):
    """Records pairwise competition results between templates."""

    __tablename__ = "template_competition_record"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    template_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    compared_against_template_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    scope_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    win_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    loss_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tie_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_score_delta: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=0)
    avg_retention_delta: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=0)
    avg_render_delta: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=0)
    avg_upload_delta: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=0)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_compared_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class TemplateLearningStat(Base):
    """Aggregated learning statistics for a template in a given scope."""

    __tablename__ = "template_learning_stat"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    template_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    scope_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rerender_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_render_score: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=0)
    avg_upload_score: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=0)
    avg_retention_score: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=0)
    avg_final_priority_score: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=0)
    success_rate: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=0)
    retry_rate: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=0)
    rerender_rate: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=0)
    avg_scene_failure_rate: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=0)
    stability_index: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=0)
    reuse_effectiveness: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=0)
    dominance_confidence: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=0)
    last_7d_score: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=0)
    updated_from_project_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class TemplateReusePreview(Base):
    """Cached preview payload for a template reuse candidate."""

    __tablename__ = "template_reuse_preview"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    template_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    preview_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    preview_payload: Mapped[Any] = mapped_column(JSON, nullable=False, default=dict)
    warnings_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    editable_fields_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


