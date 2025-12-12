"""
Player API Endpoints

Handles player character management and statistics.
Note: In this implementation, User IS the player character.
"""

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError
from . import api_v1
from .schemas import error_schema
from ..model import db, User, Encounter
from ..services.player_service import PlayerService


def _format_user_as_character(user):
    """Helper to format User as character data"""
    return {
        "id": user.id,
        "user_id": user.id,
        "char_name": user.username,
        "char_class": user.player_class_rel.name if user.player_class_rel else None,
        "char_race": user.player_race_rel.name if user.player_race_rel else None,
        "hit_points": user.hitpoints,
        "max_hit_points": user.max_hp,
        "level": user.level,
        "experience": user.exp_points,
        "armor_class": 10,
        "is_active": True,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@api_v1.route("/player/characters", methods=["GET"])
@jwt_required()
def get_characters():
    """
    Get all characters for the authenticated user

    Returns:
        200: List of player characters (single user)
    """
    current_user_id = int(get_jwt_identity())
    user = db.session.get(User, current_user_id)

    if not user:
        return jsonify({"characters": []}), 200

    return jsonify({"characters": [_format_user_as_character(user)]}), 200

    return jsonify({"characters": [_format_user_as_character(user)]}), 200

@api_v1.route("/player/characters", methods=["POST"])
@jwt_required()
def create_character():
    """
    Create/update character info for user

    Note: In this implementation, users already have a character.
    This endpoint returns 409 Conflict.
    """
    return (
        jsonify(
            error_schema.dump(
                {
                    "error": "Conflict",
                    "message": "User already has a character. Use PATCH to update.",
                    "status_code": 409,
                }
            )
        ),
        409,
    )


@api_v1.route("/player/characters/<int:character_id>", methods=["GET"])
@jwt_required()
def get_character(character_id):
    """
    Get a specific character by ID

    Returns:
        200: Character information
        403: Character belongs to another user
        404: Character not found
    """
    current_user_id = int(get_jwt_identity())
    character = db.session.get(User, character_id)

    if not character:
        return (
            jsonify(error_schema.dump({"error": "Not Found", "message": "Character not found", "status_code": 404})),
            404,
        )

    if character.id != current_user_id:
        return (
            jsonify(
                error_schema.dump(
                    {"error": "Forbidden", "message": "You do not have access to this character", "status_code": 403}
                )
            ),
            403,
        )

    # Accrue points lazily on API request
    PlayerService().accrue_points(character)
    # Include points in the character payload
    payload = _format_user_as_character(character)
    payload["points"] = character.points
    return jsonify(payload), 200


@api_v1.route("/player/characters/<int:character_id>", methods=["PATCH"])
@jwt_required()
def update_character(character_id):
    """
    Update a character's information

    Request Body:
        {
            "hit_points": int (optional),
            "experience": int (optional)
        }

    Returns:
        200: Character updated successfully
        403: Character belongs to another user
        404: Character not found
    """
    current_user_id = int(get_jwt_identity())
    character = db.session.get(User, character_id)

    if not character:
        return (
            jsonify(error_schema.dump({"error": "Not Found", "message": "Character not found", "status_code": 404})),
            404,
        )

    if character.id != current_user_id:
        return (
            jsonify(
                error_schema.dump(
                    {"error": "Forbidden", "message": "You do not have access to this character", "status_code": 403}
                )
            ),
            403,
        )

    data = request.get_json()

    try:
        # Update allowed fields
        if "hit_points" in data:
            character.hitpoints = min(data["hit_points"], character.max_hp)
        if "experience" in data:
            character.exp_points = max(0, data["experience"])

        db.session.commit()

        return (
            jsonify({"message": "Character updated successfully", "character": _format_user_as_character(character)}),
            200,
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        return (
            jsonify(
                error_schema.dump(
                    {"error": "Database Error", "message": "Failed to update character", "status_code": 500}
                )
            ),
            500,
        )


@api_v1.route("/player/characters/<int:character_id>/stats", methods=["GET"])
@jwt_required()
def get_character_stats(character_id):
    """
    Get detailed statistics for a character

    Returns:
        200: Character statistics including encounter history
        403: Character belongs to another user
        404: Character not found
    """
    current_user_id = int(get_jwt_identity())
    character = db.session.get(User, character_id)

    if not character:
        return (
            jsonify(error_schema.dump({"error": "Not Found", "message": "Character not found", "status_code": 404})),
            404,
        )

    if character.id != current_user_id:
        return (
            jsonify(
                error_schema.dump(
                    {"error": "Forbidden", "message": "You do not have access to this character", "status_code": 403}
                )
            ),
            403,
        )

    # Get encounter statistics
    # Accrue points lazily on stats request
    PlayerService().accrue_points(character)
    encounters = Encounter.query.filter_by(user_id=character_id).order_by(Encounter.created_at.desc()).all()
    total_encounters = len(encounters)
    successful_encounters = sum(1 for e in encounters if e.was_successful)
    total_damage_dealt = sum(e.damage_dealt or 0 for e in encounters)
    total_damage_received = sum(e.damage_received or 0 for e in encounters)

    # Include recent encounters and points in response
    recent = encounters[:10]
    from .schemas import EncounterSchema
    recent_encounters = EncounterSchema(many=True).dump(recent)

    character_payload = _format_user_as_character(character)
    character_payload["points"] = character.points

    return (
        jsonify(
            {
                "character": character_payload,
                "statistics": {
                    "total_encounters": total_encounters,
                    "successful_encounters": successful_encounters,
                    "success_rate": (
                        round(successful_encounters / total_encounters * 100, 2) if total_encounters > 0 else 0
                    ),
                    "total_damage_dealt": total_damage_dealt,
                    "total_damage_received": total_damage_received,
                    "average_damage_dealt": (
                        round(total_damage_dealt / total_encounters, 2) if total_encounters > 0 else 0
                    ),
                },
                "recent_encounters": recent_encounters,
            }
        ),
        200,
    )
