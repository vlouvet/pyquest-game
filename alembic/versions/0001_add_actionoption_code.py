"""add actionoption.code column and backfill

Revision ID: 0001_add_actionoption_code
Revises:
Create Date: 2025-12-10 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_add_actionoption_code"
down_revision = None
branch_labels = None


def upgrade():
    # Add nullable 'code' column if it doesn't already exist (idempotent for existing DBs)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c['name'] for c in inspector.get_columns('actionoption')] if inspector.has_table('actionoption') else []
    if 'code' not in cols:
        try:
            op.add_column("actionoption", sa.Column("code", sa.String(), nullable=True))
        except Exception:
            # In case of race conditions or concurrent migrations the column
            # may have been added after our check; ignore duplicate-column errors.
            pass
    # Backfill codes based on name (safe to run even if column exists)
    conn.execute(sa.text("UPDATE actionoption SET code = name WHERE code IS NULL"))
    # Create unique index on code if it doesn't exist
    indexes = [ix['name'] for ix in inspector.get_indexes('actionoption')]
    if op.f("ix_actionoption_code") not in indexes:
        op.create_index(op.f("ix_actionoption_code"), "actionoption", ["code"], unique=True)


def downgrade():
    op.drop_index(op.f("ix_actionoption_code"), table_name="actionoption")
    op.drop_column("actionoption", "code")
