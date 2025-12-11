"""
Combat API Endpoints

Handles combat actions and encounters.
"""

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError
from . import api_v1, limiter
from .schemas import combat_action_schema, combat_actions_schema, encounter_schema, error_schema
from ..model import db, User, Tile, CombatAction, Encounter
from ..services.combat_service import CombatService


@api_v1.route("/player/<int:player_id>/tiles/<int:tile_id>/combat-actions", methods=["GET"])
@jwt_required()
def get_combat_actions(player_id, tile_id):
    """
    Get available combat actions for a player on a specific tile

    Returns:
        200: List of available combat actions filtered by class/race
        403: Player belongs to another user
        404: Player or tile not found
    """
    current_user_id = int(get_jwt_identity())
    player = db.session.get(User, player_id)

    if not player:
        return (
            jsonify(error_schema.dump({"error": "Not Found", "message": "Player not found", "status_code": 404})),
            404,
        )

    if player.id != current_user_id:
        return (
            jsonify(
                error_schema.dump(
                    {"error": "Forbidden", "message": "You do not have access to this player", "status_code": 403}
                )
            ),
            403,
        )

    tile = db.session.get(Tile, tile_id)
    if not tile:
        return jsonify(error_schema.dump({"error": "Not Found", "message": "Tile not found", "status_code": 404})), 404

    # Get available actions
    combat_service = CombatService()
    actions = combat_service.get_available_actions(player)

    return (
        jsonify({"tile_id": tile_id, "tile_type": tile.type, "available_actions": combat_actions_schema.dump(actions)}),
        200,
    )


@api_v1.route("/player/<int:player_id>/combat/execute", methods=["POST"])
@jwt_required()
@limiter.limit("30 per minute")
def execute_combat_action_api(player_id):
    """
    Execute a combat action

    Request Body:
        {
            "tile_id": int,
            "combat_action_code": "string"
        }

    Returns:
        200: Combat result with encounter data
        400: Invalid input
        403: Player belongs to another user
        404: Player, tile, or action not found
    """
    current_user_id = int(get_jwt_identity())
    player = db.session.get(User, player_id)

    if not player:
        return (
            jsonify(error_schema.dump({"error": "Not Found", "message": "Player not found", "status_code": 404})),
            404,
        )

    if player.id != current_user_id:
        return (
            jsonify(
                error_schema.dump(
                    {"error": "Forbidden", "message": "You do not have access to this player", "status_code": 403}
                )
            ),
            403,
        )

    data = request.get_json()
    if not data or "tile_id" not in data or "combat_action_code" not in data:
        return (
            jsonify(
                error_schema.dump(
                    {
                        "error": "Bad Request",
                        "message": "tile_id and combat_action_code are required",
                        "status_code": 400,
                    }
                )
            ),
            400,
        )

    tile_id = data["tile_id"]
    combat_action_code = data["combat_action_code"]

    try:
        # Get tile
        tile = db.session.get(Tile, tile_id)
        if not tile:
            return (
                jsonify(error_schema.dump({"error": "Not Found", "message": "Tile not found", "status_code": 404})),
                404,
            )

        # Get combat action
        combat_action = CombatAction.query.filter_by(code=combat_action_code).first()
        if not combat_action:
            return (
                jsonify(
                    error_schema.dump({"error": "Not Found", "message": "Combat action not found", "status_code": 404})
                ),
                404,
            )

        # Execute combat action
        combat_service = CombatService()
        result = combat_service.execute_combat_action(player=player, tile=tile, combat_action=combat_action)

        # Convert CombatResult to dict
        result_dict = result.to_dict()

        response_data = {
            "success": result_dict.get("success", False),
            "message": result_dict.get("message", ""),
            "player_hp": player.hitpoints,
            "player_hp_change": result_dict.get("player_hp_change", 0),
            "tile_completed": result_dict.get("tile_completed", False),
        }

        # Add encounter if present (legacy support)
        if False:  # encounters are tracked but not returned in this response
            response_data["encounter"] = encounter_schema.dump(result["encounter"])

        return jsonify(response_data), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return (
            jsonify(
                error_schema.dump(
                    {"error": "Database Error", "message": "Failed to execute combat action", "status_code": 500}
                )
            ),
            500,
        )


@api_v1.route("/player/<int:player_id>/encounters", methods=["GET"])
@jwt_required()
def get_player_encounters(player_id):
    """
    Get encounter history for a player

    Query Parameters:
        limit: Maximum number of encounters to return (default: 50)
        offset: Number of encounters to skip (default: 0)

    Returns:
        200: List of encounters
        403: Player belongs to another user
        404: Player not found
    """
    current_user_id = int(get_jwt_identity())
    player = db.session.get(User, player_id)

    if not player:
        return (
            jsonify(error_schema.dump({"error": "Not Found", "message": "Player not found", "status_code": 404})),
            404,
        )

    if player.id != current_user_id:
        return (
            jsonify(
                error_schema.dump(
                    {"error": "Forbidden", "message": "You do not have access to this player", "status_code": 403}
                )
            ),
            403,
        )

    # Get pagination parameters
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)

    # Get encounters
    encounters = (
        Encounter.query.filter_by(user_id=player_id)
        .order_by(Encounter.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    total_count = Encounter.query.filter_by(user_id=player_id).count()

    from .schemas import EncounterSchema

    encounters_schema = EncounterSchema(many=True)

    return (
        jsonify(
            {"encounters": encounters_schema.dump(encounters), "total": total_count, "limit": limit, "offset": offset}
        ),
        200,
    )
