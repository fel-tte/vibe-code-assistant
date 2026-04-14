"""
Conftest for integration tests.

Uses an in-memory SQLite database so these tests run without
requiring a live Postgres instance.  Set DATABASE_URL to a real
Postgres URL before running if you want full Postgres coverage.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

# Ensure backend package is importable when pytest is invoked from the
# repository root or from the backend/ directory.
BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Point at SQLite unless the caller provided a real DATABASE_URL.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.db.base import Base  # noqa: E402 – import after sys.path fixup


@pytest.fixture(scope="session")
def db_engine():
    """Session-scoped SQLite engine with all tables created."""
    url = os.environ.get("DATABASE_URL", "sqlite:///:memory:")
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args, future=True)

    # Import only the render pipeline models (avoid Postgres-specific JSONB types
    # found in template_factory, template_runtime, veo_workspace, etc.).
    import app.models.render_job  # noqa: F401
    import app.models.render_scene_task  # noqa: F401
    import app.models.provider_webhook_event  # noqa: F401
    import app.models.state_transition_event  # noqa: F401
    import app.models.render_timeline_event  # noqa: F401
    import app.models.render_incident_state  # noqa: F401
    import app.models.render_incident_action  # noqa: F401
    import app.models.global_kill_switch  # noqa: F401
    import app.models.release_gate_state  # noqa: F401

    # Create only the tables defined by the models we imported above.
    # Passing `tables=` restricts creation to those specific tables and avoids
    # errors from Postgres-specific column types (JSONB) used by other models.
    target_tables = [
        t for t in Base.metadata.sorted_tables
        if t.name in {
            "render_jobs",
            "render_scene_tasks",
            "provider_webhook_events",
            "state_transition_events",
            "render_timeline_events",
            "render_incident_states",
            "render_incident_actions",
            "global_kill_switches",
            "release_gate_states",
        }
    ]
    Base.metadata.create_all(bind=engine, tables=target_tables)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    """
    Function-scoped transactional session that rolls back after each test,
    keeping tests isolated without dropping/recreating tables.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    factory = sessionmaker(bind=connection, autoflush=False, autocommit=False, expire_on_commit=False)
    session = factory()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
