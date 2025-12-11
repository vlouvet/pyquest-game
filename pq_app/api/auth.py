"""
Authentication API Endpoints

Handles user registration, login, and JWT token management.
"""
from flask import request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from . import api_v1, limiter
from .schemas import user_schema, error_schema
from ..model import db, User


@api_v1.route('/auth/register', methods=['POST'])
@limiter.limit("10 per minute")
def register():
    """
    Register a new user
    
    Request Body:
        {
            "username": "string",
            "email": "string",
            "password": "string"
        }
    
    Returns:
        201: User created successfully
        400: Invalid input or user already exists
    """
    data = request.get_json()
    
    if not data:
        return jsonify(error_schema.dump({
            'error': 'Bad Request',
            'message': 'No JSON data provided',
            'status_code': 400
        })), 400
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    # Validation
    if not username or not email or not password:
        return jsonify(error_schema.dump({
            'error': 'Bad Request',
            'message': 'Username, email, and password are required',
            'status_code': 400
        })), 400
    
    # Check if user exists
    if User.query.filter_by(username=username).first():
        return jsonify(error_schema.dump({
            'error': 'Conflict',
            'message': 'Username already exists',
            'status_code': 409
        })), 409
    
    if User.query.filter_by(email=email).first():
        return jsonify(error_schema.dump({
            'error': 'Conflict',
            'message': 'Email already registered',
            'status_code': 409
        })), 409
    
    try:
        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User created successfully',
            'user': user_schema.dump(user)
        }), 201
    except IntegrityError as e:
        db.session.rollback()
        return jsonify(error_schema.dump({
            'error': 'Conflict',
            'message': 'User with this username or email already exists',
            'status_code': 409
        })), 409
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify(error_schema.dump({
            'error': 'Database Error',
            'message': 'Failed to create user',
            'status_code': 500
        })), 500


@api_v1.route('/auth/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """
    Login and receive JWT tokens
    
    Request Body:
        {
            "username": "string",
            "password": "string"
        }
    
    Returns:
        200: Login successful with access and refresh tokens
        401: Invalid credentials
    """
    data = request.get_json()
    
    if not data:
        return jsonify(error_schema.dump({
            'error': 'Bad Request',
            'message': 'No JSON data provided',
            'status_code': 400
        })), 400
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify(error_schema.dump({
            'error': 'Bad Request',
            'message': 'Username and password are required',
            'status_code': 400
        })), 400
    
    try:
        # Find user
        user = User.query.filter_by(username=username).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify(error_schema.dump({
                'error': 'Unauthorized',
                'message': 'Invalid username or password',
                'status_code': 401
            })), 401
        
        # Create tokens (identity must be string)
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user_schema.dump(user)
        }), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify(error_schema.dump({
            'error': 'Database Error',
            'message': 'Failed to authenticate user',
            'status_code': 500
        })), 500


@api_v1.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token using refresh token
    
    Returns:
        200: New access token
    """
    current_user_id = get_jwt_identity()  # Already string from JWT
    access_token = create_access_token(identity=current_user_id)
    
    return jsonify({
        'access_token': access_token
    }), 200


@api_v1.route('/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current authenticated user information
    
    Returns:
        200: User information
        404: User not found
    """
    current_user_id = int(get_jwt_identity())  # Convert from string
    user = db.session.get(User, current_user_id)
    
    if not user:
        return jsonify(error_schema.dump({
            'error': 'Not Found',
            'message': 'User not found',
            'status_code': 404
        })), 404
    
    return jsonify(user_schema.dump(user)), 200
