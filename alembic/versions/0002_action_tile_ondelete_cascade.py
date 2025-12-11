"""alter action.tile FK to use ON DELETE CASCADE

Revision ID: 0002_action_tile_ondelete_cascade
Revises: 0001_add_actionoption_code
Create Date: 2025-12-10 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '0002_action_tile_ondelete_cascade'
down_revision = '0001_add_actionoption_code'
branch_labels = None


def upgrade():
    # Use reflection to find any FK constraints on 'action' that reference 'tile', drop them,
    # then create a new FK with ON DELETE CASCADE.
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    fks = inspector.get_foreign_keys('action')
    for fk in fks:
        referred_table = fk.get('referred_table') or fk.get('referredTable') or fk.get('referred')
        # Different SQLAlchemy versions/dialects return names differently; normalize
        if referred_table == 'tile' or fk.get('referred_table') == 'tile':
            constraint_name = fk.get('name')
            if constraint_name:
                try:
                    op.drop_constraint(constraint_name, 'action', type_='foreignkey')
                except Exception:
                    # if drop fails, continue to next
                    pass

    # Create new foreign key with ON DELETE CASCADE (use a clear name)
    op.create_foreign_key('fk_action_tile_tile', 'action', 'tile', ['tile'], ['id'], ondelete='CASCADE')


def downgrade():
    # Drop the cascade FK and recreate without ondelete (best-effort)
    try:
        op.drop_constraint('fk_action_tile_tile', 'action', type_='foreignkey')
    except Exception:
        pass
    op.create_foreign_key('fk_action_tile_tile', 'action', 'tile', ['tile'], ['id'])
