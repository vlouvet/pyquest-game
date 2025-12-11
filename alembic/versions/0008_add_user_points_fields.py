"""add user points fields

Revision ID: 0008_add_user_points_fields
Revises: 0007_add_monster_hp_to_tiles
Create Date: 2025-12-11
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0008_add_user_points_fields'
down_revision = '0007_add_monster_hp_to_tiles'
branch_labels = None
depends_on = None


def upgrade():
    # Add points and last_points_accrual_at to user table, skipping if already present (SQLite-friendly)
    conn = op.get_bind()
    existing_cols = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info('user')").fetchall()}
    if 'points' not in existing_cols:
        op.add_column('user', sa.Column('points', sa.Integer(), nullable=True))
    if 'last_points_accrual_at' not in existing_cols:
        op.add_column('user', sa.Column('last_points_accrual_at', sa.DateTime(), nullable=True))


def downgrade():
    # Drop columns if present
    conn = op.get_bind()
    existing_cols = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info('user')").fetchall()}
    if 'last_points_accrual_at' in existing_cols:
        op.drop_column('user', 'last_points_accrual_at')
    if 'points' in existing_cols:
        op.drop_column('user', 'points')
