"""add performance indexes

Revision ID: 20260413_0026
Revises: 20260412_9999
Create Date: 2026-04-13 00:00:00.000000
"""
from __future__ import annotations

from alembic import op

revision = "20260413_0026"
down_revision = "20260412_9999"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # render_jobs – composite index for status-based list queries
    op.create_index(
        "ix_render_job_state",
        "render_jobs",
        ["status"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_render_job_created_at",
        "render_jobs",
        ["created_at"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_render_job_project_id_status",
        "render_jobs",
        ["project_id", "status"],
        if_not_exists=True,
    )

    # render_scene_tasks – hot-path indexes for dispatch + poll queries
    op.create_index(
        "ix_render_scene_task_job_id",
        "render_scene_tasks",
        ["job_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_render_scene_task_state",
        "render_scene_tasks",
        ["status"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_render_scene_task_job_status",
        "render_scene_tasks",
        ["job_id", "status"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_render_scene_task_job_status", table_name="render_scene_tasks")
    op.drop_index("ix_render_scene_task_state", table_name="render_scene_tasks")
    op.drop_index("ix_render_scene_task_job_id", table_name="render_scene_tasks")
    op.drop_index("ix_render_job_project_id_status", table_name="render_jobs")
    op.drop_index("ix_render_job_created_at", table_name="render_jobs")
    op.drop_index("ix_render_job_state", table_name="render_jobs")
