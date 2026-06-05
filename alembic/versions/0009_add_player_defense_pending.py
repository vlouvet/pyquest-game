"""add transient player defense to tiles

Revision ID: 0009_add_player_defense_pending
Revises: 0008_add_user_points_fields
Create Date: 2026-06-04 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0009_add_player_defense_pending"
down_revision = "0008_add_user_points_fields"
branch_labels = None


def upgrade():
    """Add player_defense_pending column to tile table"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = [col["name"] for col in inspector.get_columns("tile")]

    if "player_defense_pending" not in existing_columns:
        op.add_column("tile", sa.Column("player_defense_pending", sa.Integer(), nullable=True))


def downgrade():
    """Remove player_defense_pending column from tile table"""
    op.drop_column("tile", "player_defense_pending")
