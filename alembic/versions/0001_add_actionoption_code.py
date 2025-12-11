"""add actionoption.code column and backfill

Revision ID: 0001_add_actionoption_code
Revises: 
Create Date: 2025-12-10 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String

# revision identifiers, used by Alembic.
revision = '0001_add_actionoption_code'
down_revision = None
branch_labels = None
def upgrade():
    # Add nullable 'code' column
    op.add_column('actionoption', sa.Column('code', sa.String(), nullable=True))
    # Backfill codes based on name
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE actionoption SET code = name WHERE code IS NULL"))
    # Create unique index on code
    op.create_index(op.f('ix_actionoption_code'), 'actionoption', ['code'], unique=True)


def downgrade():
    op.drop_index(op.f('ix_actionoption_code'), table_name='actionoption')
    op.drop_column('actionoption', 'code')
