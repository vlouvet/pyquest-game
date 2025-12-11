"""
TileService - Business logic for tile management and generation

This service handles:
- Tile generation with random types
- Content generation based on tile type
- Tile retrieval and validation
- Action filtering by tile type
"""

import random
from typing import Optional, List, Tuple, Dict
from flask import flash
from .. import model, gameTile, pqMonsters
from flask import current_app


class TileData:
    """Data class representing tile information"""

    def __init__(
        self,
        tile: model.Tile,
        tile_type_obj: model.TileTypeOption,
        allowed_actions: List[model.ActionOption],
        content: str = None,
    ):
        self.tile = tile
        self.tile_type_obj = tile_type_obj
        self.tile_type_name = tile_type_obj.name if tile_type_obj else None
        self.allowed_actions = allowed_actions
        self.content = content or tile.content


class TileService:
    """Service for managing tiles in the game"""

    def __init__(self, db_session=None):
        """Initialize TileService with optional database session"""
        self.db = db_session or model.db.session

    def get_tile_types(self) -> List[Dict[str, any]]:
        """Get all available tile types"""
        return [
            {"name": tile_type.name, "id": tile_type.id}
            for tile_type in model.TileTypeOption.query.order_by(model.TileTypeOption.name)
        ]

    def generate_tile_content(self, tile_type_name: str) -> str:
        """Generate content for a tile based on its type"""
        tile_config = gameTile.pqGameTile()

        if tile_type_name == "sign":
            return tile_config.generate_signpost()
        elif tile_type_name == "monster":
            monster = pqMonsters.NPCMonster()
            return f"{monster.name} ({monster.hitpoints} HP)"
        elif tile_type_name == "scene":
            return "This is a scene tile"
        elif tile_type_name == "treasure":
            return "This is a treasure tile"
        else:
            return "Unknown tile type"

    def create_tile(self, user_id: int, playthrough_id: int, tile_type_id: int = None) -> model.Tile:
        """
        Create a new tile for the player

        Args:
            user_id: The player's user ID
            playthrough_id: The active playthrough ID
            tile_type_id: Optional specific tile type ID (random if not provided)

        Returns:
            The newly created Tile object (not yet committed)
        """
        # Select random tile type if not specified
        if tile_type_id is None:
            tile_types = self.get_tile_types()
            tile_type_id = random.choice(tile_types)["id"]

        # Create the tile
        new_tile = model.Tile()
        new_tile.type = tile_type_id
        new_tile.user_id = user_id
        new_tile.playthrough_id = playthrough_id

        # Generate content based on type
        tile_type_obj = self.db.get(model.TileTypeOption, tile_type_id)
        tile_type_name = tile_type_obj.name if tile_type_obj else None
        new_tile.content = self.generate_tile_content(tile_type_name)

        # Initialize monster HP for monster tiles
        if tile_type_name == "monster":
            # Tougher monsters: configurable HP range
            cfg = current_app.config if current_app else {}
            hp_min = cfg.get("MONSTER_HP_MIN", 60)
            hp_max = cfg.get("MONSTER_HP_MAX", 120)
            multiplier = cfg.get("DIFFICULTY_MULTIPLIER", 1.0)
            base_hp = random.randint(hp_min, hp_max)
            monster_hp = int(base_hp * float(multiplier))
            new_tile.monster_max_hp = monster_hp
            new_tile.monster_current_hp = monster_hp

        return new_tile

    def get_latest_tile(self, user_id: int, playthrough_id: int = None) -> Optional[model.Tile]:
        """
        Get the most recent tile for a user

        Args:
            user_id: The player's user ID
            playthrough_id: Optional playthrough ID to filter by

        Returns:
            The most recent Tile or None
        """
        query = model.Tile.query.filter_by(user_id=user_id)

        if playthrough_id is not None:
            query = query.filter_by(playthrough_id=playthrough_id)

        return query.order_by(model.Tile.id.desc()).first()

    def get_active_playthrough(self, user_id: int) -> Optional[model.Playthrough]:
        """
        Get the active (not ended) playthrough for a user

        Args:
            user_id: The player's user ID

        Returns:
            The active Playthrough or None
        """
        return (
            model.Playthrough.query.filter_by(user_id=user_id, ended_at=None)
            .order_by(model.Playthrough.started_at.desc())
            .first()
        )

    def get_allowed_actions(self, tile_type_name: str) -> List[model.ActionOption]:
        """
        Get allowed actions for a specific tile type

        Args:
            tile_type_name: Name of the tile type (sign, monster, treasure, scene)

        Returns:
            List of allowed ActionOption objects
        """
        all_actions = model.ActionOption.query.order_by(model.ActionOption.name).all()

        if tile_type_name == "sign":
            # Sign tiles only allow rest, inspect, and quit
            return [a for a in all_actions if a.name in ["rest", "inspect", "quit"]]
        elif tile_type_name == "treasure":
            # Treasure tiles disable fight
            return [a for a in all_actions if a.name != "fight"]
        else:
            # Other tile types (monster, scene) allow all actions
            return all_actions

    def get_tile_data(self, tile_id: int) -> Optional[TileData]:
        """
        Get comprehensive tile data including type and allowed actions

        Args:
            tile_id: The tile ID

        Returns:
            TileData object or None if tile not found
        """
        tile = self.db.get(model.Tile, tile_id)
        if not tile:
            return None

        tile_type_obj = self.db.get(model.TileTypeOption, tile.type)
        tile_type_name = tile_type_obj.name if tile_type_obj else None
        allowed_actions = self.get_allowed_actions(tile_type_name)

        return TileData(tile, tile_type_obj, allowed_actions)

    def validate_tile_access(self, tile: model.Tile, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Validate that a user can access a tile

        Args:
            tile: The Tile object
            user_id: The user ID attempting to access

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not tile:
            return False, "Tile not found"

        if tile.user_id != user_id:
            return False, "Unauthorized access to tile"

        return True, None

    def needs_new_tile(self, user_id: int, playthrough_id: int) -> bool:
        """
        Check if a new tile should be generated

        Args:
            user_id: The player's user ID
            playthrough_id: The active playthrough ID

        Returns:
            True if a new tile should be generated
        """
        latest_tile = self.get_latest_tile(user_id, playthrough_id)

        # Need new tile if no tiles exist or last tile was actioned
        return latest_tile is None or latest_tile.action_taken

    def start_new_playthrough(self, user_id: int) -> Tuple[model.Playthrough, model.Tile]:
        """
        Create a new playthrough and initial tile for a player

        Args:
            user_id: The player's user ID

        Returns:
            Tuple of (new_playthrough, first_tile)
        """
        # Create new playthrough
        new_playthrough = model.Playthrough(user_id=user_id)
        self.db.add(new_playthrough)
        self.db.flush()  # Get the playthrough ID

        # Create first tile
        first_tile = self.create_tile(user_id, new_playthrough.id)
        self.db.add(first_tile)

        return new_playthrough, first_tile
