"""
API Blueprint Package

RESTful API for PyQuest mobile/external clients.
Version: 1.0
"""
from flask import Blueprint
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')
jwt = JWTManager()

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per hour", "50 per minute"],
    storage_uri="memory://",
)

# Import routes after blueprint creation to avoid circular imports
from . import auth, tiles, combat, player, docs, error_handlers

__all__ = ['api_v1', 'jwt', 'limiter']
