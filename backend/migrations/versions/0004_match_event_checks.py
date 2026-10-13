"""Track last event lookup to avoid refetching match events indefinitely.

Revision ID: 0004
Revises: 0003
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("fixture_details", sa.Column("events_checked_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column("fixture_details", "events_checked_at")
