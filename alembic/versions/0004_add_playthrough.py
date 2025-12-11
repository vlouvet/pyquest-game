"""add Playthrough model and Tile.playthrough_id

Revision ID: 0004_add_playthrough
Revises: 0003_make_actionoption_code_not_nullable
Create Date: 2025-12-11 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0004_add_playthrough'
down_revision = '0003_make_actionoption_code_not_nullable'
branch_labels = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Create playthrough table if it doesn't exist (idempotent)
    if 'playthrough' not in inspector.get_table_names():
        op.create_table(
            'playthrough',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('ended_at', sa.DateTime(), nullable=True),
        )
        # create foreign key to user
        op.create_foreign_key('fk_playthrough_user', 'playthrough', 'user', ['user_id'], ['id'])

    # Add playthrough_id column to tile table if missing
    tile_cols = []
    if 'tile' in inspector.get_table_names():
        tile_cols = [c['name'] for c in inspector.get_columns('tile')]

    if 'playthrough_id' not in tile_cols:
        op.add_column('tile', sa.Column('playthrough_id', sa.Integer(), nullable=True))
        # create fk from tile to playthrough (idempotent creation may raise if exists)
        try:
            op.create_foreign_key('fk_tile_playthrough', 'tile', 'playthrough', ['playthrough_id'], ['id'])
        except Exception:
            # Foreign key might already exist; ignore
            pass


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Remove foreign key and column from tile if they exist
    if 'tile' in inspector.get_table_names():
        cols = [c['name'] for c in inspector.get_columns('tile')]
        if 'playthrough_id' in cols:
            try:
                op.drop_constraint('fk_tile_playthrough', 'tile', type_='foreignkey')
            except Exception:
                pass
            try:
                op.drop_column('tile', 'playthrough_id')
            except Exception:
                pass

    # Drop playthrough table if it exists
    if 'playthrough' in inspector.get_table_names():
        try:
            op.drop_constraint('fk_playthrough_user', 'playthrough', type_='foreignkey')
        except Exception:
            pass
        try:
            op.drop_table('playthrough')
        except Exception:
            pass
