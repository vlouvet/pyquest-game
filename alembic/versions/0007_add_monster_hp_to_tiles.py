"""add monster HP tracking to tiles

Revision ID: 0007_add_monster_hp_to_tiles
Revises: 0006_add_combat_encounter_media_tables
Create Date: 2025-12-11 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0007_add_monster_hp_to_tiles"
down_revision = "0006_add_combat_encounter_media_tables"
branch_labels = None


def upgrade():
    """Add monster_max_hp and monster_current_hp columns to tile table"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Get existing columns
    existing_columns = [col["name"] for col in inspector.get_columns("tile")]

    # Add monster_max_hp if it doesn't exist
    if "monster_max_hp" not in existing_columns:
        op.add_column("tile", sa.Column("monster_max_hp", sa.Integer(), nullable=True))

    # Add monster_current_hp if it doesn't exist
    if "monster_current_hp" not in existing_columns:
        op.add_column("tile", sa.Column("monster_current_hp", sa.Integer(), nullable=True))


def downgrade():
    """Remove monster HP columns from tile table"""
    op.drop_column("tile", "monster_current_hp")
    op.drop_column("tile", "monster_max_hp")
