from flask import Flask
from flask_login import LoginManager
from . import model
import os


login_manager = LoginManager()


def create_app(config_name=None):
    """
    Application factory for PyQuest game.

    Args:
        config_name: Configuration to use (development, testing, production)

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)

    # Load configuration
    if config_name is None:
        config_name = os.environ.get("APP_ENV", "development")

    from config import config

    app.config.from_object(config.get(config_name, config["default"]))
    
    # JWT configuration
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', app.config['SECRET_KEY'])
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600  # 1 hour
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 2592000  # 30 days

    # Initialize extensions
    model.db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "main.login"
    
    # Initialize JWT and rate limiter
    from .api import jwt, limiter
    jwt.init_app(app)
    limiter.init_app(app)

    # Create database tables
    # In development and testing we create tables and seed defaults automatically.
    # In production environments, prefer running Alembic migrations instead.
    with app.app_context():
        if config_name in ("development", "testing"):
            model.db.create_all()
            model.init_defaults()

    # Register blueprints
    from .app import main_bp
    from .api import api_v1

    app.register_blueprint(main_bp)
    app.register_blueprint(api_v1)

    return app


@login_manager.user_loader
def load_user(user_id):
    # Use Session.get to avoid legacy Query.get API
    return model.db.session.get(model.User, int(user_id))
