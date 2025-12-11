"""
Response Schemas

Marshmallow schemas for API response serialization.
"""

from marshmallow import Schema, fields, EXCLUDE


class UserSchema(Schema):
    """User serialization schema"""

    class Meta:
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    email = fields.Email()
    created_at = fields.DateTime(dump_only=True)


class PlayerCharacterSchema(Schema):
    """Player character serialization schema"""

    class Meta:
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    char_name = fields.Str(required=True)
    char_class = fields.Str(required=True)
    char_race = fields.Str(required=True)
    hit_points = fields.Int()
    max_hit_points = fields.Int()
    level = fields.Int()
    experience = fields.Int()
    gold = fields.Int()
    armor_class = fields.Int()
    is_active = fields.Bool()
    created_at = fields.DateTime(dump_only=True)


class TileTypeOptionSchema(Schema):
    """Tile type option serialization schema"""

    class Meta:
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    name = fields.Str()
    ascii_art = fields.Str()


class ActionOptionSchema(Schema):
    """Action option serialization schema"""

    class Meta:
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    code = fields.Str()
    name = fields.Str()
    description = fields.Str()


class TileSchema(Schema):
    """Tile serialization schema"""

    class Meta:
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    id = fields.Int()
    content = fields.Str()
    playthrough_id = fields.Int()
    tile_type_obj = fields.Nested(TileTypeOptionSchema, dump_only=True)
    available_actions = fields.List(fields.Nested(ActionOptionSchema), dump_only=True)
    ascii_art = fields.Str(dump_only=True)


class CombatActionSchema(Schema):
    """Combat action serialization schema"""

    class Meta:
        unknown = EXCLUDE

    points = fields.Int()
    last_points_accrual_at = fields.DateTime(allow_none=True)

    id = fields.Int(dump_only=True)
    code = fields.Str()
    name = fields.Str()
    description = fields.Str()
    damage_min = fields.Int()
    damage_max = fields.Int()
    heal_amount = fields.Int()
    defense_boost = fields.Int()
    success_rate = fields.Int()
    requires_class = fields.Str()
    requires_race = fields.Str()


class EncounterSchema(Schema):
    """Encounter serialization schema"""

    class Meta:
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    player_id = fields.Int()
    tile_id = fields.Int()
    combat_action_id = fields.Int()
    player_hp_before = fields.Int()
    player_hp_after = fields.Int()
    damage_dealt = fields.Int()
    damage_received = fields.Int()
    was_successful = fields.Bool()
    created_at = fields.DateTime(dump_only=True)


class ActionResultSchema(Schema):
    """Action result serialization schema"""

    class Meta:
        unknown = EXCLUDE

    success = fields.Bool()
    message = fields.Str()
    player_hp = fields.Int()
    gold_change = fields.Int()
    experience_change = fields.Int()
    next_tile_id = fields.Int()
    encounter = fields.Nested(EncounterSchema, allow_none=True)


class ErrorSchema(Schema):
    """Error response schema"""

    class Meta:
        unknown = EXCLUDE

    error = fields.Str()
    message = fields.Str()
    status_code = fields.Int()


# Schema instances for reuse
user_schema = UserSchema()
users_schema = UserSchema(many=True)
player_schema = PlayerCharacterSchema()
players_schema = PlayerCharacterSchema(many=True)
tile_schema = TileSchema()
tiles_schema = TileSchema(many=True)
combat_action_schema = CombatActionSchema()
combat_actions_schema = CombatActionSchema(many=True)
encounter_schema = EncounterSchema()
action_result_schema = ActionResultSchema()
error_schema = ErrorSchema()
