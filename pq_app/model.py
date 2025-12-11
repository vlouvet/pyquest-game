from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

db = SQLAlchemy()


# Ensure SQLite enforces foreign key constraints when used as the runtime database.
@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    # Only apply for sqlite connections
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# Provide a concrete Model reference to satisfy static analyzers
Model = db.Model


class User(Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String)
    hitpoints = db.Column(db.Integer, default=100)
    max_hp = db.Column(db.Integer, default=100)
    strength = db.Column(db.Integer, default=10)
    intelligence = db.Column(db.Integer, default=10)
    stealth = db.Column(db.Integer, default=10)
    exp_points = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    playerclass = db.Column(db.Integer, db.ForeignKey("playerclass.id"))
    playerrace = db.Column(db.Integer, db.ForeignKey("playerrace.id"))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    tiles = db.relationship("Tile", backref="user", lazy=True)
    player_class_rel = db.relationship("PlayerClass", backref="users", foreign_keys=[playerclass])
    player_race_rel = db.relationship("PlayerRace", backref="users", foreign_keys=[playerrace])

    def __init__(
        self,
        username=None,
        password_hash=None,
        email=None,
        hitpoints=None,
        playerclass=None,
        playerrace=None,
    ):
        self.username = username
        self.password_hash = password_hash
        self.email = email
        if hitpoints is not None:
            self.hitpoints = hitpoints
        self.playerclass = playerclass
        self.playerrace = playerrace

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        # If there is no stored password hash, return False instead of passing None
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def is_alive(self):
        """Check if player is still alive"""
        return self.hitpoints > 0

    def take_damage(self, amount):
        """Reduce hitpoints by damage amount, minimum 0"""
        self.hitpoints = max(0, self.hitpoints - amount)

    def heal(self, amount):
        """Heal hitpoints, maximum max_hp"""
        self.hitpoints = min(self.max_hp, self.hitpoints + amount)


class Tile(Model):
    id = db.Column(db.Integer, primary_key=True)
    action_taken = db.Column(db.Boolean, default=False)
    type = db.Column(db.Integer, db.ForeignKey("tiletypeoption.id"), nullable=False)
    action = db.Column(db.Integer, db.ForeignKey("action.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    playthrough_id = db.Column(db.Integer, db.ForeignKey("playthrough.id"), nullable=True)
    content = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Monster combat tracking (for monster tiles)
    monster_max_hp = db.Column(db.Integer, nullable=True)  # Monster's maximum HP
    monster_current_hp = db.Column(db.Integer, nullable=True)  # Monster's current HP (null for non-monster tiles)

    # Relationships - specify foreign_keys to resolve ambiguity
    tile_type = db.relationship("TileTypeOption", foreign_keys=[type], backref="tiles")
    tile_action = db.relationship("Action", foreign_keys=[action], backref="tiles")
    playthrough = db.relationship("Playthrough", foreign_keys=[playthrough_id], backref="tiles")

    def __init__(
        self,
        user_id=None,
        type=None,
        action=None,
        content=None,
        action_taken=False,
        playthrough_id=None,
        monster_max_hp=None,
        monster_current_hp=None,
    ):
        self.user_id = user_id
        self.type = type
        self.action = action
        self.content = content
        self.action_taken = action_taken
        self.playthrough_id = playthrough_id
        self.monster_max_hp = monster_max_hp
        self.monster_current_hp = monster_current_hp

    @property
    def is_monster_alive(self) -> bool:
        """Check if the monster on this tile is still alive"""
        return self.monster_current_hp is not None and self.monster_current_hp > 0

    @property
    def monster_hp_percent(self) -> float:
        """Get monster HP as a percentage (0.0 to 1.0)"""
        if self.monster_max_hp and self.monster_current_hp is not None:
            return max(0.0, min(1.0, self.monster_current_hp / self.monster_max_hp))
        return 0.0


class Action(Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    tile = db.Column(db.Integer, db.ForeignKey("tile.id", use_alter=True, ondelete="CASCADE"))
    actionverb = db.Column(db.Integer, db.ForeignKey("actionoption.id"))

    # Relationships - specify foreign_keys to avoid circular reference issues
    tile_ref = db.relationship("Tile", foreign_keys=[tile], passive_deletes=True)
    action_option = db.relationship("ActionOption", backref="actions")


class ActionOption(Model):
    __tablename__ = "actionoption"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    code = db.Column(db.String, unique=True, nullable=True)

    def __init__(self, name=None):
        self.name = name


class TileTypeOption(Model):
    __tablename__ = "tiletypeoption"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    ascii_art = db.Column(db.Text, nullable=True)

    def __init__(self, name=None, ascii_art=None):
        self.name = name
        self.ascii_art = ascii_art


class PlayerClass(Model):
    __tablename__ = "playerclass"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    def __init__(self, name=None):
        self.name = name


class PlayerRace(Model):
    __tablename__ = "playerrace"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    def __init__(self, name=None):
        self.name = name

    def __repr__(self):
        return f"<PlayerRace {self.name}>"


class Playthrough(Model):
    __tablename__ = "playthrough"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    started_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    ended_at = db.Column(db.DateTime, nullable=True)

    # relationship back to user and tiles
    user = db.relationship("User", backref="playthroughs")

    def __init__(self, user_id=None):
        self.user_id = user_id


class CombatAction(Model):
    """
    Combat actions available to players during encounters.
    Examples: attack_light, attack_heavy, defend, heal, flee, special_ability
    These extend beyond basic ActionOption to provide detailed combat mechanics.
    """

    __tablename__ = "combataction"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    damage_min = db.Column(db.Integer, default=0)  # Minimum damage dealt (0 for non-attack actions)
    damage_max = db.Column(db.Integer, default=0)  # Maximum damage dealt
    heal_amount = db.Column(db.Integer, default=0)  # HP healed (for heal actions)
    defense_boost = db.Column(db.Integer, default=0)  # Defense modifier
    requires_class = db.Column(db.Integer, db.ForeignKey("playerclass.id"), nullable=True)  # Class-specific actions
    requires_race = db.Column(db.Integer, db.ForeignKey("playerrace.id"), nullable=True)  # Race-specific actions
    success_rate = db.Column(db.Integer, default=100)  # Percentage chance of success (1-100)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    required_class = db.relationship("PlayerClass", foreign_keys=[requires_class])
    required_race = db.relationship("PlayerRace", foreign_keys=[requires_race])

    def __init__(
        self,
        name=None,
        code=None,
        description=None,
        damage_min=0,
        damage_max=0,
        heal_amount=0,
        defense_boost=0,
        requires_class=None,
        requires_race=None,
        success_rate=100,
    ):
        self.name = name
        self.code = code
        self.description = description
        self.damage_min = damage_min
        self.damage_max = damage_max
        self.heal_amount = heal_amount
        self.defense_boost = defense_boost
        self.requires_class = requires_class
        self.requires_race = requires_race
        self.success_rate = success_rate


class Encounter(Model):
    """
    Tracks combat encounters between players and monsters.
    Records detailed combat history including multiple combat actions within a single tile.
    """

    __tablename__ = "encounter"
    id = db.Column(db.Integer, primary_key=True)
    tile_id = db.Column(db.Integer, db.ForeignKey("tile.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    combat_action_id = db.Column(db.Integer, db.ForeignKey("combataction.id"), nullable=True)
    player_hp_before = db.Column(db.Integer, nullable=False)  # Player HP before this action
    player_hp_after = db.Column(db.Integer, nullable=False)  # Player HP after this action
    monster_hp_before = db.Column(db.Integer, nullable=True)  # Monster HP before (if applicable)
    monster_hp_after = db.Column(db.Integer, nullable=True)  # Monster HP after (if applicable)
    damage_dealt = db.Column(db.Integer, default=0)  # Damage dealt by player
    damage_received = db.Column(db.Integer, default=0)  # Damage received by player
    was_successful = db.Column(db.Boolean, default=True)  # Did the action succeed?
    result_message = db.Column(db.Text, nullable=True)  # Description of what happened
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    tile = db.relationship("Tile", backref="encounters")
    user = db.relationship("User", backref="encounters")
    combat_action = db.relationship("CombatAction", backref="encounters")

    def __init__(
        self,
        tile_id=None,
        user_id=None,
        combat_action_id=None,
        player_hp_before=0,
        player_hp_after=0,
        monster_hp_before=None,
        monster_hp_after=None,
        damage_dealt=0,
        damage_received=0,
        was_successful=True,
        result_message=None,
    ):
        self.tile_id = tile_id
        self.user_id = user_id
        self.combat_action_id = combat_action_id
        self.player_hp_before = player_hp_before
        self.player_hp_after = player_hp_after
        self.monster_hp_before = monster_hp_before
        self.monster_hp_after = monster_hp_after
        self.damage_dealt = damage_dealt
        self.damage_received = damage_received
        self.was_successful = was_successful
        self.result_message = result_message


class TileMedia(Model):
    """
    Media assets (images, ASCII art) associated with tiles or tile types.
    Allows multiple media items per tile type and supports future image uploads.
    """

    __tablename__ = "tilemedia"
    id = db.Column(db.Integer, primary_key=True)
    tile_type_id = db.Column(db.Integer, db.ForeignKey("tiletypeoption.id"), nullable=True)
    tile_id = db.Column(db.Integer, db.ForeignKey("tile.id", ondelete="CASCADE"), nullable=True)
    media_type = db.Column(db.String(50), nullable=False)  # 'ascii_art', 'image', 'animation'
    content = db.Column(db.Text, nullable=True)  # ASCII art content or file path for images
    url = db.Column(db.String(500), nullable=True)  # External URL or local file path
    is_default = db.Column(db.Boolean, default=False)  # Is this the default media for the type?
    display_order = db.Column(db.Integer, default=0)  # Order for multiple media items
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    tile_type = db.relationship("TileTypeOption", backref="media")
    tile = db.relationship("Tile", backref="media")

    def __init__(
        self,
        tile_type_id=None,
        tile_id=None,
        media_type=None,
        content=None,
        url=None,
        is_default=False,
        display_order=0,
    ):
        self.tile_type_id = tile_type_id
        self.tile_id = tile_id
        self.media_type = media_type
        self.content = content
        self.url = url
        self.is_default = is_default
        self.display_order = display_order


def init_defaults():
    """pre-populate action options and combat actions tables"""
    if ActionOption.query.first() is None:
        action_options = [
            {"name": "rest", "code": "rest"},
            {"name": "inspect", "code": "inspect"},
            {"name": "fight", "code": "fight"},
            {"name": "quit", "code": "quit"},
        ]
        for act_opt in action_options:
            current_act_opt = ActionOption()
            current_act_opt.name = act_opt["name"]
            current_act_opt.code = act_opt.get("code")
            db.session.add(current_act_opt)
        db.session.commit()

    if TileTypeOption.query.first() is None:
        tile_types = [
            {"name": "scene"},
            {"name": "monster"},
            {"name": "sign"},
            {"name": "treasure"},
        ]
        for tile_type in tile_types:
            current_tile_type = TileTypeOption()
            current_tile_type.name = tile_type["name"]
            db.session.add(current_tile_type)
        db.session.commit()

    if PlayerClass.query.first() is None:
        player_classes = [{"name": "witch"}, {"name": "fighter"}, {"name": "healer"}]
        for pc in player_classes:
            current_class = PlayerClass()
            current_class.name = pc["name"]
            db.session.add(current_class)
        db.session.commit()

    if PlayerRace.query.first() is None:
        player_races = [{"name": "Human"}, {"name": "Elf"}, {"name": "Pandarian"}]
        for pr in player_races:
            current_race = PlayerRace()
            current_race.name = pr["name"]
            db.session.add(current_race)
        db.session.commit()

    # Seed CombatAction data for enhanced combat system
    if CombatAction.query.first() is None:
        combat_actions = [
            # Basic actions available to all
            {
                "name": "Light Attack",
                "code": "attack_light",
                "description": "A quick, nimble strike with lower damage but higher accuracy",
                "damage_min": 3,
                "damage_max": 8,
                "success_rate": 95,
            },
            {
                "name": "Heavy Attack",
                "code": "attack_heavy",
                "description": "A powerful strike that deals more damage but may miss",
                "damage_min": 8,
                "damage_max": 15,
                "success_rate": 75,
            },
            {
                "name": "Defend",
                "code": "defend",
                "description": "Take a defensive stance, reducing incoming damage",
                "defense_boost": 5,
                "success_rate": 100,
            },
            {
                "name": "Heal",
                "code": "heal",
                "description": "Restore health using basic first aid",
                "heal_amount": 15,
                "success_rate": 100,
            },
            {"name": "Flee", "code": "flee", "description": "Attempt to escape from combat", "success_rate": 60},
            # Class-specific actions (will need class IDs after PlayerClass seeding)
            {
                "name": "Fireball",
                "code": "fireball",
                "description": "Unleash a magical fireball (Witch only)",
                "damage_min": 12,
                "damage_max": 20,
                "success_rate": 85,
                "requires_class": "witch",  # Will be converted to ID
            },
            {
                "name": "Power Strike",
                "code": "power_strike",
                "description": "A devastating blow using combat training (Fighter only)",
                "damage_min": 15,
                "damage_max": 25,
                "success_rate": 80,
                "requires_class": "fighter",
            },
            {
                "name": "Divine Heal",
                "code": "divine_heal",
                "description": "Channel divine energy to restore significant health (Healer only)",
                "heal_amount": 30,
                "success_rate": 100,
                "requires_class": "healer",
            },
            # Race-specific actions
            {
                "name": "Elven Grace",
                "code": "elven_grace",
                "description": "Use natural agility to dodge and counter (Elf only)",
                "damage_min": 5,
                "damage_max": 12,
                "defense_boost": 3,
                "success_rate": 90,
                "requires_race": "elf",
            },
            {
                "name": "Pandarian Calm",
                "code": "pandarian_calm",
                "description": "Inner peace grants defense and minor healing (Pandarian only)",
                "heal_amount": 10,
                "defense_boost": 4,
                "success_rate": 100,
                "requires_race": "pandarian",
            },
        ]

        # Get class and race IDs for foreign key references
        class_map = {pc.name.lower(): pc.id for pc in PlayerClass.query.all()}
        race_map = {pr.name.lower(): pr.id for pr in PlayerRace.query.all()}

        for action_data in combat_actions:
            combat_action = CombatAction()
            combat_action.name = action_data["name"]
            combat_action.code = action_data["code"]
            combat_action.description = action_data.get("description")
            combat_action.damage_min = action_data.get("damage_min", 0)
            combat_action.damage_max = action_data.get("damage_max", 0)
            combat_action.heal_amount = action_data.get("heal_amount", 0)
            combat_action.defense_boost = action_data.get("defense_boost", 0)
            combat_action.success_rate = action_data.get("success_rate", 100)

            # Convert class/race names to IDs
            if "requires_class" in action_data:
                combat_action.requires_class = class_map.get(action_data["requires_class"])
            if "requires_race" in action_data:
                combat_action.requires_race = race_map.get(action_data["requires_race"])

            db.session.add(combat_action)

        db.session.commit()


def user_exists(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return True
    else:
        return False
