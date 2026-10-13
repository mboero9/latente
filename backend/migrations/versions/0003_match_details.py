"""Eventos, once inicial y calificaciones observadas de cada partido."""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "fixture_details",
        sa.Column("source", sa.String(length=8), nullable=False),
        sa.Column("fixture_id", sa.Integer(), nullable=False),
        sa.Column("events", sa.JSON(), nullable=False),
        sa.Column("lineups", sa.JSON(), nullable=False),
        sa.Column("player_ratings", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source", "fixture_id"], ["fixtures.source", "fixtures.id"]),
        sa.PrimaryKeyConstraint("source", "fixture_id"),
    )


def downgrade():
    op.drop_table("fixture_details")
