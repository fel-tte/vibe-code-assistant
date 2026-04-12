"""merge remaining 0024 into 9999

Revision ID: 20260412_9998
Revises: 20260412_0024, 20260412_9999
Create Date: 2026-04-12 20:25:00.000000
"""

revision = "20260412_9998"
down_revision = (
    "20260412_0024",
    "20260412_9999",
)
branch_labels = None
depends_on = None


def upgrade():
    # IMPORTANT: no-op merge
    pass


def downgrade():
    pass
