"""Estadísticas de partido persistidas por fuente y encuentro."""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "fixture_statistics",
        sa.Column("source", sa.String(length=8), nullable=False),
        sa.Column("fixture_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source", "fixture_id"], ["fixtures.source", "fixtures.id"]),
        sa.PrimaryKeyConstraint("source", "fixture_id"),
    )


def downgrade():
    op.drop_table("fixture_statistics")
