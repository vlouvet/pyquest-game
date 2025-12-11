"""
Tile API Endpoints

Handles tile retrieval and navigation.
"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError
from . import api_v1
from .schemas import tile_schema, tiles_schema, action_result_schema, error_schema
from ..model import db, User, Tile, Playthrough
from ..services.tile_service import TileService
from ..services.media_service import MediaService


@api_v1.route('/player/<int:player_id>/tiles/current', methods=['GET'])
@jwt_required()
def get_current_tile(player_id):
    """
    Get the current tile for a player's active playthrough
    
    Returns:
        200: Current tile information with ASCII art
        403: Player belongs to another user
        404: Player or playthrough not found
    """
    current_user_id = int(get_jwt_identity())
    player = db.session.get(User, player_id)
    
    if not player:
        return jsonify(error_schema.dump({
            'error': 'Not Found',
            'message': 'Player not found',
            'status_code': 404
        })), 404
    
    if player.id != current_user_id:
        return jsonify(error_schema.dump({
            'error': 'Forbidden',
            'message': 'You do not have access to this player',
            'status_code': 403
        })), 403
    
    # Get active playthrough
    playthrough = Playthrough.query.filter_by(
        user_id=player_id,
        ended_at=None
    ).first()
    
    if not playthrough:
        return jsonify(error_schema.dump({
            'error': 'Not Found',
            'message': 'No active playthrough found',
            'status_code': 404
        })), 404
    
    # Get current tile
    tile_service = TileService()
    current_tile = tile_service.get_latest_tile(player_id, playthrough.id)
    
    if not current_tile:
        return jsonify(error_schema.dump({
            'error': 'Not Found',
            'message': 'Current tile not found',
            'status_code': 404
        })), 404
    
    tile_data = tile_service.get_tile_data(current_tile.id)
    
    # Get ASCII art
    media_service = MediaService()
    ascii_art = media_service.get_tile_display_media(current_tile.id)
    
    result = tile_schema.dump(tile_data.tile)
    result['tile_type_obj'] = {
        'id': tile_data.tile_type_obj.id,
        'name': tile_data.tile_type_obj.name,
        'ascii_art': tile_data.tile_type_obj.ascii_art
    }
    result['available_actions'] = [
        {'id': a.id, 'code': a.code, 'name': a.name}
        for a in tile_data.allowed_actions
    ]
    result['ascii_art'] = ascii_art
    
    return jsonify(result), 200


@api_v1.route('/player/<int:player_id>/tiles/<int:tile_id>', methods=['GET'])
@jwt_required()
def get_tile(player_id, tile_id):
    """
    Get a specific tile by ID
    
    Returns:
        200: Tile information with ASCII art
        403: Player belongs to another user
        404: Player or tile not found
    """
    current_user_id = int(get_jwt_identity())
    player = db.session.get(User, player_id)
    
    if not player:
        return jsonify(error_schema.dump({
            'error': 'Not Found',
            'message': 'Player not found',
            'status_code': 404
        })), 404
    
    if player.id != current_user_id:
        return jsonify(error_schema.dump({
            'error': 'Forbidden',
            'message': 'You do not have access to this player',
            'status_code': 403
        })), 403
    
    # Get tile
    tile_service = TileService()
    tile_data = tile_service.get_tile_data(tile_id)
    
    if not tile_data:
        return jsonify(error_schema.dump({
            'error': 'Not Found',
            'message': 'Tile not found',
            'status_code': 404
        })), 404
    
    # Get ASCII art
    media_service = MediaService()
    ascii_art = media_service.get_tile_display_media(tile_id)
    
    result = tile_schema.dump(tile_data.tile)
    result['tile_type_obj'] = {
        'id': tile_data.tile_type_obj.id,
        'name': tile_data.tile_type_obj.name,
        'ascii_art': tile_data.tile_type_obj.ascii_art
    }
    result['available_actions'] = [
        {'id': a.id, 'code': a.code, 'name': a.name}
        for a in tile_data.allowed_actions
    ]
    result['ascii_art'] = ascii_art
    
    return jsonify(result), 200


@api_v1.route('/player/<int:player_id>/tiles/<int:tile_id>/action', methods=['POST'])
@jwt_required()
def execute_tile_action(player_id, tile_id):
    """
    Execute an action on a tile
    
    Request Body:
        {
            "action_code": "string",
            "combat_action_code": "string" (optional, for combat actions)
        }
    
    Returns:
        200: Action result with updated player state
        400: Invalid action
        403: Player belongs to another user
        404: Player or tile not found
    """
    current_user_id = int(get_jwt_identity())
    player = db.session.get(User, player_id)
    
    if not player:
        return jsonify(error_schema.dump({
            'error': 'Not Found',
            'message': 'Player not found',
            'status_code': 404
        })), 404
    
    if player.id != current_user_id:
        return jsonify(error_schema.dump({
            'error': 'Forbidden',
            'message': 'You do not have access to this player',
            'status_code': 403
        })), 403
    
    data = request.get_json()
    if not data or 'action_code' not in data:
        return jsonify(error_schema.dump({
            'error': 'Bad Request',
            'message': 'action_code is required',
            'status_code': 400
        })), 400
    
    action_code = data['action_code']
    combat_action_code = data.get('combat_action_code')
    
    # Get tile service
    tile_service = TileService()
    tile_data = tile_service.get_tile_data(tile_id)
    
    if not tile_data:
        return jsonify(error_schema.dump({
            'error': 'Not Found',
            'message': 'Tile not found',
            'status_code': 404
        })), 404
    
    # Execute action using combat service
    from ..services.combat_service import CombatService
    combat_service = CombatService()
    
    result = combat_service.execute_action(
        player_char=player,
        tile=tile_data.tile,
        action_code=action_code,
        combat_action_code=combat_action_code
    )
    
    # Prepare response
    response_data = {
        'success': result.get('success', False),
        'message': result.get('message', ''),
        'player_hp': player.hit_points,
        'gold_change': result.get('gold_change', 0),
        'experience_change': result.get('experience_change', 0),
        'next_tile_id': None
    }
    
    # Add encounter if present
    if 'encounter' in result and result['encounter']:
        from .schemas import encounter_schema
        response_data['encounter'] = encounter_schema.dump(result['encounter'])
    
    return jsonify(response_data), 200


@api_v1.route('/player/<int:player_id>/tiles/next', methods=['POST'])
@jwt_required()
def advance_to_next_tile(player_id):
    """
    Advance player to the next tile
    
    Returns:
        200: New tile information
        403: Player belongs to another user
        404: Player or playthrough not found
    """
    current_user_id = int(get_jwt_identity())
    player = db.session.get(User, player_id)
    
    if not player:
        return jsonify(error_schema.dump({
            'error': 'Not Found',
            'message': 'Player not found',
            'status_code': 404
        })), 404
    
    if player.id != current_user_id:
        return jsonify(error_schema.dump({
            'error': 'Forbidden',
            'message': 'You do not have access to this player',
            'status_code': 403
        })), 403
    
    # Get active playthrough
    playthrough = Playthrough.query.filter_by(
        user_id=player_id,
        ended_at=None
    ).first()
    
    if not playthrough:
        return jsonify(error_schema.dump({
            'error': 'Not Found',
            'message': 'No active playthrough found',
            'status_code': 404
        })), 404
    
    try:
        # Create new tile using tile service
        tile_service = TileService()
        new_tile = tile_service.generate_next_tile(playthrough.id)
        
        db.session.commit()
        
        # Get tile data for display
        tile_data = tile_service.get_tile_data(new_tile.id)
        
        # Get ASCII art
        media_service = MediaService()
        ascii_art = media_service.get_tile_display_media(new_tile.id)
        
        result = tile_schema.dump(tile_data.tile)
        result['tile_type_obj'] = {
            'id': tile_data.tile_type_obj.id,
            'name': tile_data.tile_type_obj.name,
            'ascii_art': tile_data.tile_type_obj.ascii_art
        }
        result['available_actions'] = [
            {'id': a.id, 'code': a.code, 'name': a.name}
            for a in tile_data.allowed_actions
        ]
        result['ascii_art'] = ascii_art
        
        return jsonify(result), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify(error_schema.dump({
            'error': 'Database Error',
            'message': 'Failed to advance to next tile',
            'status_code': 500
        })), 500
