"""Multisport persistent datasets and usage quotas.

Revision ID: 0005
Revises: 0004
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sport_snapshots",
        sa.Column("sport", sa.String(20), primary_key=True),
        sa.Column("dataset", sa.String(20), primary_key=True),
        sa.Column("ref", sa.String(90), primary_key=True),
        sa.Column("provider", sa.String(30), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("source_count", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.String(250)),
    )
    op.create_table(
        "sport_quotas",
        sa.Column("sport", sa.String(20), primary_key=True),
        sa.Column("day", sa.Date(), primary_key=True),
        sa.Column("requests", sa.Integer(), nullable=False),
    )


def downgrade():
    op.drop_table("sport_quotas")
    op.drop_table("sport_snapshots")
