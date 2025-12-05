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

    # Initialize extensions
    model.db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "main.login"

    # Create database tables
    with app.app_context():
        model.db.create_all()
        model.init_defaults()

    # Register blueprints
    from .app import main_bp

    app.register_blueprint(main_bp)

    return app


@login_manager.user_loader
def load_user(user_id):
    return model.User.query.get(int(user_id))
