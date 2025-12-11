"""
Combat Service - Handle all combat/encounter logic

This service extracts combat logic from routes to make it reusable
for both web UI and future API endpoints.
"""

import random
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime, timezone
from flask import flash
from sqlalchemy import select, or_

from .. import model


class CombatResult:
    """Represents the result of a combat action"""

    def __init__(
        self,
        success: bool,
        message: str,
        player_hp_change: int = 0,
        player_alive: bool = True,
        tile_completed: bool = True,
        should_end_playthrough: bool = False,
        redirect_url: Optional[str] = None,
    ):
        self.success = success
        self.message = message
        self.player_hp_change = player_hp_change
        self.player_alive = player_alive
        self.tile_completed = tile_completed
        self.should_end_playthrough = should_end_playthrough
        self.redirect_url = redirect_url

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON responses"""
        return {
            "success": self.success,
            "message": self.message,
            "player_hp_change": self.player_hp_change,
            "player_alive": self.player_alive,
            "tile_completed": self.tile_completed,
            "should_end_playthrough": self.should_end_playthrough,
            "redirect_url": self.redirect_url,
        }


class CombatService:
    """Service for handling combat and tile action logic"""

    def __init__(self, db_session=None):
        """Initialize combat service with optional db session"""
        self.db = db_session or model.db.session

    def get_action_by_value(self, action_value: str) -> Optional[model.ActionOption]:
        """
        Resolve ActionOption by code, id, or name

        Args:
            action_value: The action value from form/API (code, id, or name)

        Returns:
            ActionOption instance or None if not found
        """
        # Try lookup by code first
        action_option = model.ActionOption.query.filter_by(code=action_value).one_or_none()

        # Fallback to numeric id
        if not action_option and action_value and action_value.isdigit():
            action_option = self.db.get(model.ActionOption, int(action_value))

        # Last resort: lookup by name
        if not action_option:
            action_option = model.ActionOption.query.filter_by(name=action_value).one_or_none()

        return action_option

    def get_tile_with_lock(self, tile_id: int) -> Optional[model.Tile]:
        """
        Get tile with row-level lock for transaction safety

        Args:
            tile_id: ID of the tile

        Returns:
            Tile instance or None
        """
        stmt = select(model.Tile).where(model.Tile.id == tile_id).with_for_update()
        return self.db.execute(stmt).scalar_one_or_none()

    def validate_tile_action(self, tile: model.Tile) -> Tuple[bool, Optional[str]]:
        """
        Check if tile can be actioned

        Args:
            tile: The tile to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not tile:
            return False, "Tile not found"

        if tile.action_taken:
            return False, "Tile already actioned"

        return True, None

    def get_available_actions(
        self, player: model.User, tile_type_name: Optional[str] = None, include_basic: bool = True
    ) -> List[model.CombatAction]:
        """
        Get combat actions available to player based on class, race, and context.

        Filters CombatActions by:
        - Player class (requires_class filter)
        - Player race (requires_race filter)
        - Tile type context (combat actions on monster tiles, etc.)

        Args:
            player: User/player instance
            tile_type_name: Optional tile type for context-based filtering
            include_basic: Include actions with no class/race requirements

        Returns:
            List of CombatAction records sorted by name
        """
        query = model.CombatAction.query

        # Filter by class: include if no requirement OR matches player's class
        class_filter = or_(
            model.CombatAction.requires_class.is_(None), model.CombatAction.requires_class == player.playerclass
        )

        # Filter by race: include if no requirement OR matches player's race
        race_filter = or_(
            model.CombatAction.requires_race.is_(None), model.CombatAction.requires_race == player.playerrace
        )

        query = query.filter(class_filter, race_filter)

        # Context-based filtering
        if tile_type_name == "monster":
            # On monster tiles, show attack and defense actions
            # Exclude pure healing actions that don't make sense in combat
            pass  # All actions are valid in combat for now
        elif tile_type_name and tile_type_name != "monster":
            # On non-monster tiles, maybe only show flee, heal, inspect-like actions
            # For now, allow all actions
            pass

        return query.order_by(model.CombatAction.name).all()

    def execute_combat_action(
        self, player: model.User, tile: model.Tile, combat_action: model.CombatAction, monster_hp: int = None
    ) -> CombatResult:
        """
        Execute a CombatAction with full mechanics:
        - Roll success based on success_rate
        - Calculate damage (random between min/max)
        - Apply healing
        - Update persistent monster HP on tile
        - Track encounter in Encounter table

        Args:
            player: User/player instance
            tile: Tile instance
            combat_action: CombatAction to execute
            monster_hp: Current monster HP (uses tile.monster_current_hp if not provided)

        Returns:
            CombatResult with action outcome
        """
        # Use tile's persistent monster HP if available, otherwise default
        if monster_hp is None:
            monster_hp = tile.monster_current_hp if tile.monster_current_hp is not None else 50

        # Store player HP before action
        hp_before = player.hitpoints

        # Roll for success
        roll = random.randint(1, 100)
        success = roll <= combat_action.success_rate

        damage_dealt = 0
        damage_received = 0
        hp_change = 0
        message = ""
        monster_defeated = False

        if not success:
            # Action failed
            message = f"{combat_action.name} failed! (Rolled {roll}, needed {combat_action.success_rate} or less)"
            flash(message)
        else:
            # Action succeeded
            parts = []

            # Calculate damage dealt (if attack action)
            if combat_action.damage_max > 0:
                damage_dealt = random.randint(combat_action.damage_min, combat_action.damage_max)
                parts.append(f"dealt {damage_dealt} damage")

                # Update monster HP on tile
                new_monster_hp = max(0, monster_hp - damage_dealt)
                if tile.monster_current_hp is not None:
                    tile.monster_current_hp = new_monster_hp

                    # Check if monster is defeated
                    if new_monster_hp <= 0:
                        monster_defeated = True
                        parts.append("Monster defeated!")
                    else:
                        parts.append(f"Monster HP: {new_monster_hp}/{tile.monster_max_hp}")

                # Monster counter-attack (only if monster is alive)
                if new_monster_hp > 0 and random.randint(1, 100) <= 50:
                    damage_received = random.randint(3, 10)
                    player.take_damage(damage_received)
                    hp_change -= damage_received
                    parts.append(f"received {damage_received} damage")

            # Apply healing
            if combat_action.heal_amount > 0:
                healed = min(combat_action.heal_amount, player.max_hp - player.hitpoints)
                player.heal(combat_action.heal_amount)
                hp_change += healed
                parts.append(f"healed {healed} HP")

            # Note defense boost (not yet implemented in player state)
            if combat_action.defense_boost > 0:
                parts.append(f"gained +{combat_action.defense_boost} defense")

            message = f"{combat_action.name}: " + ", ".join(parts) + "!"
            flash(message)

        # Calculate final monster HP after action
        final_monster_hp = (
            tile.monster_current_hp if tile.monster_current_hp is not None else max(0, monster_hp - damage_dealt)
        )

        # Create Encounter record
        encounter = model.Encounter(
            tile_id=tile.id,
            user_id=player.id,
            combat_action_id=combat_action.id,
            player_hp_before=hp_before,
            player_hp_after=player.hitpoints,
            monster_hp_before=monster_hp,
            monster_hp_after=final_monster_hp,
            damage_dealt=damage_dealt,
            damage_received=damage_received,
            was_successful=success,
            result_message=message,
        )
        self.db.add(encounter)

        return CombatResult(
            success=success,
            message=message,
            player_hp_change=hp_change,
            player_alive=player.is_alive,
            tile_completed=monster_defeated,  # Only complete tile when monster is defeated
        )

    def get_or_create_action_record(
        self, tile_id: int, action_name: str, action_option: Optional[model.ActionOption]
    ) -> int:
        """
        Get existing action record or create new one

        Args:
            tile_id: ID of the tile
            action_name: Name of the action
            action_option: ActionOption instance

        Returns:
            Action record ID
        """
        actionverb_id = action_option.id if action_option else None

        # Check if action record already exists
        if actionverb_id is not None:
            action_record = model.Action.query.filter_by(tile=tile_id, actionverb=actionverb_id).first()

            if action_record:
                return action_record.id

        # Create new action record
        new_action = model.Action()
        new_action.name = action_name
        new_action.tile = tile_id
        new_action.actionverb = actionverb_id
        self.db.add(new_action)
        self.db.flush()

        return new_action.id

    def execute_action(
        self,
        player: model.User,
        tile: model.Tile,
        action_name: str,
        tile_type_name: Optional[str] = None,
        combat_action_code: Optional[str] = None,
    ) -> CombatResult:
        """
        Execute a combat/tile action. Routes to either legacy actions (rest, fight, inspect, quit)
        or new CombatAction system.

        Args:
            player: User/player instance
            tile: Tile instance
            action_name: Name of the action to execute
            tile_type_name: Type of tile (monster, treasure, etc.)
            combat_action_code: Optional CombatAction code for enhanced combat

        Returns:
            CombatResult with action outcome
        """
        if tile_type_name is None and tile.tile_type:
            tile_type_name = tile.tile_type.name

        # Check if this is a CombatAction code
        if combat_action_code:
            combat_action = model.CombatAction.query.filter_by(code=combat_action_code).first()
            if combat_action:
                return self.execute_combat_action(player, tile, combat_action)

        # Execute legacy action based on type
        if action_name == "rest":
            return self._execute_rest(player, tile_type_name)
        elif action_name == "fight":
            return self._execute_fight(player, tile_type_name)
        elif action_name == "inspect":
            return self._execute_inspect(player, tile_type_name)
        elif action_name == "quit":
            return self._execute_quit(player, tile)
        else:
            # Try to match as CombatAction by name
            combat_action = model.CombatAction.query.filter_by(name=action_name).first()
            if combat_action:
                return self.execute_combat_action(player, tile, combat_action)

            # Unknown action - default behavior
            return CombatResult(success=True, message=f"Performed action: {action_name}", tile_completed=True)

    def _execute_rest(self, player: model.User, tile_type_name: str) -> CombatResult:
        """Execute rest action"""
        # Check if resting on a monster tile
        if tile_type_name == "monster":
            # Lose 50% of HP or 10 HP, whichever is greater
            damage = max(int(player.hitpoints * 0.5), 10)
            player.take_damage(damage)
            message = f"Resting near a monster is dangerous! You lost {damage} HP."
            flash(message)

            return CombatResult(
                success=True,
                message=message,
                player_hp_change=-damage,
                player_alive=player.is_alive,
                tile_completed=True,
            )
        else:
            # Safe rest - heal 10 HP
            heal_amount = 10
            player.heal(heal_amount)
            message = f"You rest and recover {heal_amount} HP."
            flash(message)

            return CombatResult(
                success=True, message=message, player_hp_change=heal_amount, player_alive=True, tile_completed=True
            )

    def _execute_fight(self, player: model.User, tile_type_name: str) -> CombatResult:
        """Execute fight action"""
        damage = random.randint(5, 20)
        player.take_damage(damage)
        message = f"You fought bravely and took {damage} damage!"
        flash(message)

        return CombatResult(
            success=True, message=message, player_hp_change=-damage, player_alive=player.is_alive, tile_completed=True
        )

    def _execute_inspect(self, player: model.User, tile_type_name: str) -> CombatResult:
        """Execute inspect action"""
        if tile_type_name == "monster":
            message = "You carefully observe the creature, learning its patterns."
            flash(message)

            return CombatResult(
                success=True, message=message, player_hp_change=0, player_alive=True, tile_completed=True
            )

        elif tile_type_name == "treasure":
            # 1% chance to restore all HP
            if random.randint(1, 100) == 1:
                max_hp = player.max_hp
                healed = max_hp - player.hitpoints
                player.hitpoints = max_hp
                message = f"You found a magical healing artifact! Restored {healed} HP to full health!"
                flash(message)

                return CombatResult(
                    success=True, message=message, player_hp_change=healed, player_alive=True, tile_completed=True
                )
            else:
                message = "You inspect the area and find hints of treasure nearby."
                flash(message)

                return CombatResult(
                    success=True, message=message, player_hp_change=0, player_alive=True, tile_completed=True
                )
        else:
            message = "You take a moment to examine your surroundings carefully."
            flash(message)

            return CombatResult(
                success=True, message=message, player_hp_change=0, player_alive=True, tile_completed=True
            )

    def _execute_quit(self, player: model.User, tile: model.Tile) -> CombatResult:
        """Execute quit action - end the playthrough"""
        message = "You decide to retreat from this challenge."
        flash(message)

        # Mark the playthrough as ended
        playthrough_ended = False
        try:
            if tile and tile.playthrough_id:
                pt = self.db.get(model.Playthrough, tile.playthrough_id)
                if pt:
                    pt.ended_at = datetime.now(timezone.utc)
                    self.db.add(pt)
                    playthrough_ended = True
        except Exception:
            # Don't let playthrough ending failures block the response
            self.db.rollback()

        return CombatResult(
            success=True,
            message=message,
            player_hp_change=0,
            player_alive=True,
            tile_completed=True,
            should_end_playthrough=True,
        )

    def complete_tile_action(self, tile: model.Tile, player: model.User, action_history_id: int) -> None:
        """
        Mark tile as completed with action history

        Args:
            tile: Tile to complete
            player: Player who completed it
            action_history_id: ID of the action record
        """
        tile.user_id = player.id
        tile.action = action_history_id
        tile.action_taken = True
        self.db.add(tile)
        self.db.add(player)
