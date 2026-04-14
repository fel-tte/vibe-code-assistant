#!/usr/bin/env python3
"""Verify database state and schema"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import inspect, text
from app.db.session import engine
from app.models import RenderJob, RenderSceneTask  # noqa: F401


def verify_tables():
    """Verify all required tables exist"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    required_tables = [
        "render_job",
        "render_scene_task",
        "provider_webhook_event",
        "state_transition_event",
    ]

    missing = [t for t in required_tables if t not in tables]

    if missing:
        print(f"❌ Missing tables: {missing}")
        return False

    print(f"✅ All {len(required_tables)} required tables exist")
    return True


def verify_indexes():
    """Verify performance indexes"""
    inspector = inspect(engine)

    # Check render_job indexes
    job_indexes = inspector.get_indexes("render_job")
    job_index_names = [idx["name"] for idx in job_indexes]

    required_job_indexes = ["ix_render_job_state", "ix_render_job_created_at"]

    for idx in required_job_indexes:
        if idx not in job_index_names:
            print(f"⚠️ Missing index: {idx}")

    print("✅ Database indexes verified")
    return True


def verify_migration_head():
    """Verify single migration head"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        heads = [row[0] for row in result]

    if len(heads) != 1:
        print(f"❌ Expected 1 migration head, found {len(heads)}: {heads}")
        return False

    print(f"✅ Single migration head: {heads[0]}")
    return True


def main():
    print("🔍 Verifying database state...\n")

    checks = [
        ("Tables", verify_tables),
        ("Indexes", verify_indexes),
        ("Migration Head", verify_migration_head),
    ]

    all_passed = True

    for name, check_fn in checks:
        try:
            if not check_fn():
                all_passed = False
        except Exception as e:
            print(f"❌ {name} check failed: {e}")
            all_passed = False

    print()

    if all_passed:
        print("✅ Database state verified")
        sys.exit(0)
    else:
        print("❌ Database verification failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
