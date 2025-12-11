"""
Global Error Handlers for API

Provides centralized error handling for all API endpoints.
"""
from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException
from flask_jwt_extended.exceptions import JWTExtendedException
from . import api_v1
from .schemas import error_schema
from ..model import db


@api_v1.errorhandler(400)
def bad_request_error(error):
    """Handle 400 Bad Request errors"""
    return jsonify(error_schema.dump({
        'error': 'Bad Request',
        'message': str(error.description) if hasattr(error, 'description') else 'Invalid request',
        'status_code': 400
    })), 400


@api_v1.errorhandler(401)
def unauthorized_error(error):
    """Handle 401 Unauthorized errors"""
    return jsonify(error_schema.dump({
        'error': 'Unauthorized',
        'message': str(error.description) if hasattr(error, 'description') else 'Authentication required',
        'status_code': 401
    })), 401


@api_v1.errorhandler(JWTExtendedException)
def jwt_error(error):
    """Handle JWT-related errors"""
    return jsonify(error_schema.dump({
        'error': 'Unauthorized',
        'message': str(error),
        'status_code': 401
    })), 401


@api_v1.errorhandler(403)
def forbidden_error(error):
    """Handle 403 Forbidden errors"""
    return jsonify(error_schema.dump({
        'error': 'Forbidden',
        'message': str(error.description) if hasattr(error, 'description') else 'Access denied',
        'status_code': 403
    })), 403


@api_v1.errorhandler(404)
def not_found_error(error):
    """Handle 404 Not Found errors"""
    return jsonify(error_schema.dump({
        'error': 'Not Found',
        'message': str(error.description) if hasattr(error, 'description') else 'Resource not found',
        'status_code': 404
    })), 404


@api_v1.errorhandler(409)
def conflict_error(error):
    """Handle 409 Conflict errors"""
    return jsonify(error_schema.dump({
        'error': 'Conflict',
        'message': str(error.description) if hasattr(error, 'description') else 'Resource conflict',
        'status_code': 409
    })), 409


@api_v1.errorhandler(422)
def unprocessable_entity_error(error):
    """Handle 422 Unprocessable Entity errors"""
    return jsonify(error_schema.dump({
        'error': 'Unprocessable Entity',
        'message': str(error.description) if hasattr(error, 'description') else 'Invalid data',
        'status_code': 422
    })), 422


@api_v1.errorhandler(429)
def rate_limit_error(error):
    """Handle 429 Too Many Requests errors"""
    return jsonify(error_schema.dump({
        'error': 'Too Many Requests',
        'message': 'Rate limit exceeded. Please try again later.',
        'status_code': 429
    })), 429


@api_v1.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server errors"""
    return jsonify(error_schema.dump({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred',
        'status_code': 500
    })), 500


@api_v1.errorhandler(ValidationError)
def validation_error(error):
    """Handle Marshmallow validation errors"""
    return jsonify(error_schema.dump({
        'error': 'Validation Error',
        'message': str(error.messages),
        'status_code': 422
    })), 422


@api_v1.errorhandler(IntegrityError)
def integrity_error(error):
    """Handle database integrity errors"""
    from ..model import db
    db.session.rollback()
    
    # Extract meaningful message
    message = 'Database integrity constraint violated'
    if 'UNIQUE constraint failed' in str(error):
        message = 'Duplicate entry - resource already exists'
    elif 'FOREIGN KEY constraint failed' in str(error):
        message = 'Invalid reference - related resource not found'
    elif 'NOT NULL constraint failed' in str(error):
        message = 'Required field is missing'
    
    return jsonify(error_schema.dump({
        'error': 'Integrity Error',
        'message': message,
        'status_code': 409
    })), 409


@api_v1.errorhandler(SQLAlchemyError)
def database_error(error):
    """Handle general database errors"""
    from ..model import db
    db.session.rollback()
    
    return jsonify(error_schema.dump({
        'error': 'Database Error',
        'message': 'A database error occurred',
        'status_code': 500
    })), 500


@api_v1.errorhandler(HTTPException)
def http_exception_error(error):
    """Handle all other HTTP exceptions"""
    return jsonify(error_schema.dump({
        'error': error.name,
        'message': error.description,
        'status_code': error.code
    })), error.code


@api_v1.errorhandler(Exception)
def unhandled_exception(error):
    """Handle any unhandled exceptions"""
    from ..model import db
    db.session.rollback()
    
    # Log the error in production
    import traceback
    print(f"Unhandled exception: {error}")
    print(traceback.format_exc())
    
    return jsonify(error_schema.dump({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred',
        'status_code': 500
    })), 500
