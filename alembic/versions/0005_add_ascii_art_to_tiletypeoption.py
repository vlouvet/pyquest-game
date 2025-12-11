"""add ascii_art column to TileTypeOption

Revision ID: 0005_add_ascii_art
Revises: 0004_add_playthrough
Create Date: 2025-12-11 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0005_add_ascii_art'
down_revision = '0004_add_playthrough'
branch_labels = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Add ascii_art column to tiletypeoption table if missing
    if 'tiletypeoption' in inspector.get_table_names():
        cols = [c['name'] for c in inspector.get_columns('tiletypeoption')]
        
        if 'ascii_art' not in cols:
            op.add_column('tiletypeoption', sa.Column('ascii_art', sa.Text(), nullable=True))


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Remove ascii_art column from tiletypeoption table if it exists
    if 'tiletypeoption' in inspector.get_table_names():
        cols = [c['name'] for c in inspector.get_columns('tiletypeoption')]
        
        if 'ascii_art' in cols:
            op.drop_column('tiletypeoption', 'ascii_art')
