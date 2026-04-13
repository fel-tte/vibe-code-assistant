"""
Integration tests for the render pipeline.

These tests exercise the database layer and service functions with a real
(in-memory SQLite) database session.  Celery tasks and external provider
calls are replaced by direct service-layer calls so the suite runs without
Docker or network access.

Mark: @pytest.mark.integration
Run:  pytest backend/tests/integration/ -v -m integration
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sqlalchemy.orm import Session

from app.models.render_job import RenderJob
from app.models.render_scene_task import RenderSceneTask
from app.services.render_repository import (
    create_render_job_with_scenes,
    get_render_job_by_id,
    get_scene_task_by_id,
    list_queued_scene_tasks,
)


pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_scene_payload(index: int = 1, provider: str = "runway") -> dict[str, Any]:
    return {
        "scene_index": index,
        "title": f"Integration scene {index}",
        "provider": provider,
        "script_text": f"A cinematic integration test shot, scene {index}.",
        "prompt_text": f"Integration test prompt {index}",
        "resolved_prompt_text": f"Integration test prompt {index}",
        "provider_target_duration_sec": 5,
        "duration_seconds": 5,
        "resolved_duration_seconds": 5,
        "aspect_ratio": "16:9",
        "negative_prompt": None,
        "seed": None,
        "enable_audio": False,
        "prompt_image_url": None,
        "prompt_image_gcs_uri": None,
        "last_frame_image_url": None,
        "last_frame_image_gcs_uri": None,
        "metadata": {},
    }


# ---------------------------------------------------------------------------
# Schema / creation tests
# ---------------------------------------------------------------------------

class TestRenderJobCreation:
    """Database creation tests – no workers, no providers."""

    def test_create_single_scene_job(self, db_session: Session):
        """create_render_job_with_scenes stores job + scene in the database."""
        job = create_render_job_with_scenes(
            db_session,
            project_id="integration-test-project",
            provider="runway",
            aspect_ratio="16:9",
            style_preset=None,
            subtitle_mode="soft",
            planned_scenes=[_make_scene_payload(1)],
        )

        assert job is not None
        assert job.id is not None
        assert job.project_id == "integration-test-project"
        assert job.provider == "runway"
        assert job.status == "queued"
        assert job.planned_scene_count == 1
        assert job.completed_scene_count == 0
        assert job.failed_scene_count == 0

        reloaded = get_render_job_by_id(db_session, job.id, with_scenes=True)
        assert reloaded is not None
        assert len(reloaded.scenes) == 1
        scene = reloaded.scenes[0]
        assert scene.job_id == job.id
        assert scene.scene_index == 1
        assert scene.status == "queued"

    def test_create_multi_scene_job(self, db_session: Session):
        """All scenes are stored and linked to the parent job."""
        scenes = [_make_scene_payload(i) for i in range(1, 4)]
        job = create_render_job_with_scenes(
            db_session,
            project_id="multi-scene-project",
            provider="kling",
            aspect_ratio="9:16",
            style_preset=None,
            subtitle_mode="none",
            planned_scenes=scenes,
        )

        assert job.planned_scene_count == 3
        assert len(job.scenes) == 3

        # Scene indexes should be stored correctly
        stored_indexes = sorted(s.scene_index for s in job.scenes)
        assert stored_indexes == [1, 2, 3]

    def test_scene_request_payload_is_valid_json(self, db_session: Session):
        """Each scene's request_payload_json must be valid JSON."""
        payload = _make_scene_payload(1)
        job = create_render_job_with_scenes(
            db_session,
            project_id="json-test-project",
            provider="runway",
            aspect_ratio="16:9",
            style_preset=None,
            subtitle_mode="soft",
            planned_scenes=[payload],
        )

        for scene in job.scenes:
            parsed = json.loads(scene.request_payload_json)
            assert isinstance(parsed, dict)
            assert parsed["scene_index"] == 1

    def test_get_render_job_by_id_not_found(self, db_session: Session):
        """Returns None for unknown job IDs."""
        result = get_render_job_by_id(db_session, "nonexistent-id-xyz")
        assert result is None

    def test_list_queued_scene_tasks_returns_only_queued(self, db_session: Session):
        """list_queued_scene_tasks filters by status == 'queued'."""
        scenes = [_make_scene_payload(i) for i in range(1, 3)]
        job = create_render_job_with_scenes(
            db_session,
            project_id="queue-filter-project",
            provider="runway",
            aspect_ratio="16:9",
            style_preset=None,
            subtitle_mode="soft",
            planned_scenes=scenes,
        )

        queued = list_queued_scene_tasks(db_session, job.id)
        assert len(queued) == 2

        # Manually mark one scene as processing
        first_scene = queued[0]
        first_scene.status = "processing"
        db_session.commit()

        queued_after = list_queued_scene_tasks(db_session, job.id)
        assert len(queued_after) == 1
        assert queued_after[0].id != first_scene.id


# ---------------------------------------------------------------------------
# State-transition tests
# ---------------------------------------------------------------------------

class TestRenderJobStateTransitions:
    """Verify manual state transitions are persisted correctly."""

    def test_job_status_update_persists(self, db_session: Session):
        """Updating job.status is reflected in subsequent queries."""
        job = create_render_job_with_scenes(
            db_session,
            project_id="state-transition-project",
            provider="runway",
            aspect_ratio="16:9",
            style_preset=None,
            subtitle_mode="soft",
            planned_scenes=[_make_scene_payload(1)],
        )

        job.status = "processing"
        db_session.commit()

        reloaded = get_render_job_by_id(db_session, job.id)
        assert reloaded.status == "processing"

    def test_scene_completion_updates_counters(self, db_session: Session):
        """Completing a scene and updating counters is reflected correctly."""
        scenes = [_make_scene_payload(i) for i in range(1, 3)]
        job = create_render_job_with_scenes(
            db_session,
            project_id="counter-update-project",
            provider="runway",
            aspect_ratio="16:9",
            style_preset=None,
            subtitle_mode="soft",
            planned_scenes=scenes,
        )

        # Simulate scene 1 completing
        scene = job.scenes[0]
        scene.status = "succeeded"
        scene.output_video_url = "https://example.invalid/video1.mp4"
        scene.finished_at = datetime.utcnow()

        job.completed_scene_count = 1
        job.status = "processing"
        db_session.commit()

        reloaded = get_render_job_by_id(db_session, job.id, with_scenes=True)
        assert reloaded.completed_scene_count == 1
        assert reloaded.status == "processing"

        succeeded_scenes = [s for s in reloaded.scenes if s.status == "succeeded"]
        assert len(succeeded_scenes) == 1

    def test_full_job_completion_state(self, db_session: Session):
        """All scenes succeeded → job can be marked completed with output URL."""
        job = create_render_job_with_scenes(
            db_session,
            project_id="completion-project",
            provider="runway",
            aspect_ratio="16:9",
            style_preset=None,
            subtitle_mode="soft",
            planned_scenes=[_make_scene_payload(1)],
        )

        scene = job.scenes[0]
        scene.status = "succeeded"
        scene.output_video_url = "https://example.invalid/final.mp4"
        scene.finished_at = datetime.utcnow()

        job.status = "completed"
        job.completed_scene_count = 1
        job.output_url = "https://example.invalid/final.mp4"
        job.final_video_url = "https://example.invalid/final.mp4"
        job.completed_at = datetime.utcnow()
        db_session.commit()

        reloaded = get_render_job_by_id(db_session, job.id, with_scenes=True)
        assert reloaded.status == "completed"
        assert reloaded.output_url is not None
        assert reloaded.completed_at is not None


# ---------------------------------------------------------------------------
# Concurrent job tests
# ---------------------------------------------------------------------------

class TestConcurrentJobs:
    """Simulate multiple jobs created in the same session."""

    def test_five_concurrent_jobs_all_created(self, db_session: Session):
        """Five jobs can be created independently without collisions."""
        job_ids = []
        for i in range(5):
            job = create_render_job_with_scenes(
                db_session,
                project_id=f"concurrent-project-{i}",
                provider="runway",
                aspect_ratio="16:9",
                style_preset=None,
                subtitle_mode="soft",
                planned_scenes=[_make_scene_payload(1)],
            )
            job_ids.append(job.id)

        # All IDs should be unique
        assert len(set(job_ids)) == 5

        # All should be retrievable
        for job_id in job_ids:
            reloaded = get_render_job_by_id(db_session, job_id)
            assert reloaded is not None
            assert reloaded.status == "queued"

    def test_jobs_with_different_providers(self, db_session: Session):
        """Jobs with different providers are stored with correct provider names."""
        providers = ["runway", "kling", "veo"]
        jobs = []
        for provider in providers:
            job = create_render_job_with_scenes(
                db_session,
                project_id=f"multi-provider-{provider}",
                provider=provider,
                aspect_ratio="16:9",
                style_preset=None,
                subtitle_mode="soft",
                planned_scenes=[_make_scene_payload(1, provider=provider)],
            )
            jobs.append(job)

        stored_providers = {get_render_job_by_id(db_session, j.id).provider for j in jobs}
        assert stored_providers == set(providers)


# ---------------------------------------------------------------------------
# Error recovery tests
# ---------------------------------------------------------------------------

class TestErrorRecovery:
    """Test that error states are persisted and readable."""

    def test_job_error_state_persists_message(self, db_session: Session):
        """A job marked with an error state stores the error message."""
        job = create_render_job_with_scenes(
            db_session,
            project_id="error-recovery-project",
            provider="runway",
            aspect_ratio="16:9",
            style_preset=None,
            subtitle_mode="soft",
            planned_scenes=[_make_scene_payload(1)],
        )

        job.status = "failed"
        job.error_message = "Provider timeout after 120 seconds"
        db_session.commit()

        reloaded = get_render_job_by_id(db_session, job.id)
        assert reloaded.status == "failed"
        assert "timeout" in (reloaded.error_message or "")

    def test_scene_failure_records_error_info(self, db_session: Session):
        """A failed scene records error_message and failure_code."""
        job = create_render_job_with_scenes(
            db_session,
            project_id="scene-failure-project",
            provider="runway",
            aspect_ratio="16:9",
            style_preset=None,
            subtitle_mode="soft",
            planned_scenes=[_make_scene_payload(1)],
        )

        scene = job.scenes[0]
        scene.status = "failed"
        scene.error_message = "NSFW content detected by provider"
        scene.failure_code = "nsfw_rejected"
        scene.failure_category = "content_policy"
        scene.finished_at = datetime.utcnow()

        job.status = "failed"
        job.failed_scene_count = 1
        db_session.commit()

        reloaded_scene = get_scene_task_by_id(db_session, scene.id)
        assert reloaded_scene.status == "failed"
        assert reloaded_scene.failure_code == "nsfw_rejected"
        assert reloaded_scene.failure_category == "content_policy"


# ---------------------------------------------------------------------------
# Database state / schema validation tests
# ---------------------------------------------------------------------------

class TestDatabaseSchema:
    """Verify critical columns and constraints exist on the models."""

    def test_render_job_has_required_columns(self, db_session: Session):
        """RenderJob model has the columns required by the render pipeline."""
        job = RenderJob(
            id=str(uuid.uuid4()),
            project_id="schema-test",
            provider="runway",
            status="queued",
            aspect_ratio="16:9",
            subtitle_mode="soft",
            planned_scene_count=1,
            completed_scene_count=0,
            failed_scene_count=0,
        )
        db_session.add(job)
        db_session.flush()

        assert job.id is not None
        # created_at may be None before flush on SQLite; verify field exists
        assert hasattr(job, "created_at")
        assert hasattr(job, "output_url")
        assert hasattr(job, "final_video_url")
        assert hasattr(job, "error_message")
        assert hasattr(job, "completed_at")
        assert hasattr(job, "health_status")

    def test_render_scene_task_has_required_columns(self, db_session: Session):
        """RenderSceneTask model exposes all provider runtime fields."""
        job = RenderJob(
            id=str(uuid.uuid4()),
            project_id="schema-scene-test",
            provider="runway",
            status="queued",
            aspect_ratio="16:9",
            subtitle_mode="soft",
            planned_scene_count=1,
            completed_scene_count=0,
            failed_scene_count=0,
        )
        db_session.add(job)
        db_session.flush()

        scene = RenderSceneTask(
            id=str(uuid.uuid4()),
            job_id=job.id,
            scene_index=1,
            title="Schema test scene",
            provider="runway",
            status="queued",
            request_payload_json="{}",
        )
        db_session.add(scene)
        db_session.flush()

        assert hasattr(scene, "provider_task_id")
        assert hasattr(scene, "provider_operation_name")
        assert hasattr(scene, "output_video_url")
        assert hasattr(scene, "storage_key")
        assert hasattr(scene, "error_message")
        assert hasattr(scene, "failure_code")
        assert hasattr(scene, "retry_count")
