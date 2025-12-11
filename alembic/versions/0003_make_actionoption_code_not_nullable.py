"""make ActionOption.code non-nullable

Revision ID: 0003_make_actionoption_code_not_nullable
Revises: 0002_action_tile_ondelete_cascade
Create Date: 2025-12-10 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0003_make_actionoption_code_not_nullable'
down_revision = '0002_action_tile_ondelete_cascade'
branch_labels = None


def upgrade():
    # Ensure no NULL codes remain (previous migration backfilled code = name)
    # Then alter the column to be non-nullable. Use batch mode for all dialects
    # to ensure SQLite compatibility (it will recreate the table).
    with op.batch_alter_table('actionoption') as batch_op:
        batch_op.alter_column('code', existing_type=sa.String(), nullable=False)


def downgrade():
    # Revert the NOT NULL change using batch mode to support SQLite.
    with op.batch_alter_table('actionoption') as batch_op:
        batch_op.alter_column('code', existing_type=sa.String(), nullable=True)
