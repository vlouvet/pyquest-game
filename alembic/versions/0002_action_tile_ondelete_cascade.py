"""alter action.tile FK to use ON DELETE CASCADE

Revision ID: 0002_action_tile_ondelete_cascade
Revises: 0001_add_actionoption_code
Create Date: 2025-12-10 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_action_tile_ondelete_cascade'
down_revision = '0001_add_actionoption_code'
branch_labels = None


def upgrade():
    # Attempt to drop common FK names, then create a new FK with ON DELETE CASCADE
    conn = op.get_bind()
    # Try common constraint names; if they don't exist, ignore errors
    try:
        op.drop_constraint('action_tile_fkey', 'action', type_='foreignkey')
    except Exception:
        pass
    try:
        op.drop_constraint('fk_action_tile_tile', 'action', type_='foreignkey')
    except Exception:
        pass

    # Create new foreign key with ON DELETE CASCADE
    op.create_foreign_key('fk_action_tile_tile', 'action', 'tile', ['tile'], ['id'], ondelete='CASCADE')


def downgrade():
    # Drop the cascade FK and recreate without ondelete (best-effort)
    try:
        op.drop_constraint('fk_action_tile_tile', 'action', type_='foreignkey')
    except Exception:
        pass
    op.create_foreign_key('fk_action_tile_tile', 'action', 'tile', ['tile'], ['id'])
