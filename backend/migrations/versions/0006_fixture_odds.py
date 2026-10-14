"""Snapshots 1X2 del proveedor; las probabilidades son implícitas, no predicciones."""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "fixture_odds",
        sa.Column("source", sa.String(8), nullable=False),
        sa.Column("fixture_id", sa.Integer(), nullable=False),
        sa.Column("market", sa.String(12), nullable=False),
        sa.Column("quotations", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("source", "fixture_id", "market"),
        sa.ForeignKeyConstraint(["source", "fixture_id"], ["fixtures.source", "fixtures.id"]),
    )

def downgrade():
    op.drop_table("fixture_odds")
