from .model import *
from .userCharacter import *
from .gameforms import *
from .pqMonsters import *
from .gameTile import *
import random
from flask import Flask
from flask_login import LoginManager
from . import model

login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = random.randbytes(24).hex()
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pyquest_game.db"
    model.db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "main.login"

    with app.app_context():
        model.db.create_all()
        model.init_defaults()

    # Register the blueprint
    from .app import main_bp

    app.register_blueprint(main_bp)

    return app
