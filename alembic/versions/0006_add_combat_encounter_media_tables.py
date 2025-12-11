"""add CombatAction, Encounter, and TileMedia tables

Revision ID: 0006_add_combat_encounter_media_tables
Revises: 0005_add_ascii_art
Create Date: 2025-12-11 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0006_add_combat_encounter_media_tables'
down_revision = '0005_add_ascii_art'
branch_labels = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # Create combataction table if it doesn't exist
    if 'combataction' not in existing_tables:
        op.create_table(
            'combataction',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('code', sa.String(50), unique=True, nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('damage_min', sa.Integer(), default=0),
            sa.Column('damage_max', sa.Integer(), default=0),
            sa.Column('heal_amount', sa.Integer(), default=0),
            sa.Column('defense_boost', sa.Integer(), default=0),
            sa.Column('requires_class', sa.Integer(), nullable=True),
            sa.Column('requires_race', sa.Integer(), nullable=True),
            sa.Column('success_rate', sa.Integer(), default=100),
            sa.Column('created_at', sa.DateTime(), nullable=True),
        )
        # Add foreign keys
        try:
            op.create_foreign_key('fk_combataction_playerclass', 'combataction', 'playerclass', 
                                ['requires_class'], ['id'])
        except Exception:
            pass
        try:
            op.create_foreign_key('fk_combataction_playerrace', 'combataction', 'playerrace', 
                                ['requires_race'], ['id'])
        except Exception:
            pass

    # Create encounter table if it doesn't exist
    if 'encounter' not in existing_tables:
        op.create_table(
            'encounter',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('tile_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('combat_action_id', sa.Integer(), nullable=True),
            sa.Column('player_hp_before', sa.Integer(), nullable=False),
            sa.Column('player_hp_after', sa.Integer(), nullable=False),
            sa.Column('monster_hp_before', sa.Integer(), nullable=True),
            sa.Column('monster_hp_after', sa.Integer(), nullable=True),
            sa.Column('damage_dealt', sa.Integer(), default=0),
            sa.Column('damage_received', sa.Integer(), default=0),
            sa.Column('was_successful', sa.Boolean(), default=True),
            sa.Column('result_message', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
        )
        # Add foreign keys
        try:
            op.create_foreign_key('fk_encounter_tile', 'encounter', 'tile', 
                                ['tile_id'], ['id'], ondelete='CASCADE')
        except Exception:
            pass
        try:
            op.create_foreign_key('fk_encounter_user', 'encounter', 'user', 
                                ['user_id'], ['id'])
        except Exception:
            pass
        try:
            op.create_foreign_key('fk_encounter_combataction', 'encounter', 'combataction', 
                                ['combat_action_id'], ['id'])
        except Exception:
            pass

    # Create tilemedia table if it doesn't exist
    if 'tilemedia' not in existing_tables:
        op.create_table(
            'tilemedia',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('tile_type_id', sa.Integer(), nullable=True),
            sa.Column('tile_id', sa.Integer(), nullable=True),
            sa.Column('media_type', sa.String(50), nullable=False),
            sa.Column('content', sa.Text(), nullable=True),
            sa.Column('url', sa.String(500), nullable=True),
            sa.Column('is_default', sa.Boolean(), default=False),
            sa.Column('display_order', sa.Integer(), default=0),
            sa.Column('created_at', sa.DateTime(), nullable=True),
        )
        # Add foreign keys
        try:
            op.create_foreign_key('fk_tilemedia_tiletypeoption', 'tilemedia', 'tiletypeoption', 
                                ['tile_type_id'], ['id'])
        except Exception:
            pass
        try:
            op.create_foreign_key('fk_tilemedia_tile', 'tilemedia', 'tile', 
                                ['tile_id'], ['id'], ondelete='CASCADE')
        except Exception:
            pass


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # Drop tables in reverse order (respecting foreign key dependencies)
    if 'encounter' in existing_tables:
        op.drop_table('encounter')
    
    if 'tilemedia' in existing_tables:
        op.drop_table('tilemedia')
    
    if 'combataction' in existing_tables:
        op.drop_table('combataction')
