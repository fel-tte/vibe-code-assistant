#!/usr/bin/env python3
"""Collect database metrics for reporting"""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import text
from app.db.session import SessionLocal


def collect_metrics():
    """Collect various database metrics"""
    session = SessionLocal()

    try:
        metrics = {}

        # Row counts
        metrics["render_jobs_total"] = session.execute(
            text("SELECT COUNT(*) FROM render_jobs")
        ).scalar()

        metrics["render_scenes_total"] = session.execute(
            text("SELECT COUNT(*) FROM render_scene_tasks")
        ).scalar()

        # Status distribution
        metrics["jobs_by_state"] = {}
        result = session.execute(
            text("SELECT status, COUNT(*) FROM render_jobs GROUP BY status")
        )
        for row in result:
            metrics["jobs_by_state"][row[0]] = row[1]

        # Database size (Postgres specific)
        try:
            size_result = session.execute(
                text("SELECT pg_database_size(current_database())")
            )
            metrics["database_size_bytes"] = size_result.scalar()
        except Exception:
            metrics["database_size_bytes"] = None

        print(json.dumps(metrics, indent=2))

        return metrics

    finally:
        session.close()


if __name__ == "__main__":
    collect_metrics()
