from __future__ import annotations

from app.db.base import Base
from app.db.session import engine
import app.models  # noqa: F401


def main() -> int:
    print("Bootstrapping database schema from SQLAlchemy metadata...")
    Base.metadata.create_all(bind=engine)
    print("SQLAlchemy metadata bootstrap completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())