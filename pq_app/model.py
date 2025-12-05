from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String)
    hitpoints = db.Column(db.Integer)
    tiles = db.relationship("Tile", backref="user")
    playerclass = db.Column(db.Integer, db.ForeignKey("playerclass.id"))
    playerrace = db.Column(db.Integer, db.ForeignKey("playerrace.id"))

    def __init__(
        self, username=None, password_hash=None, email=None, hitpoints=None, playerclass=None, playerrace=None
    ):
        self.username = username
        self.password_hash = password_hash
        self.email = email
        self.hitpoints = hitpoints
        self.playerclass = playerclass
        self.playerrace = playerrace

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)


class Tile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action_taken = db.Column(db.Boolean, default=False)
    type = db.Column(db.Integer, db.ForeignKey("tiletypeoption.id"), nullable=False)
    action = db.Column(db.Integer, db.ForeignKey("action.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    content = db.Column(db.String)

    def __init__(self, user_id=None, type=None, action=None, content=None, action_taken=False):
        self.user_id = user_id
        self.type = type
        self.action = action
        self.content = content
        self.action_taken = action_taken


class Action(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    tile = db.Column(db.Integer, db.ForeignKey("tile.id"))
    actionverb = db.Column(db.Integer, db.ForeignKey("actionoption.id"))


class ActionOption(db.Model):
    __tablename__ = "actionoption"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)


class TileTypeOption(db.Model):
    __tablename__ = "tiletypeoption"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    def __init__(self, name=None):
        self.name = name


class PlayerClass(db.Model):
    __tablename__ = "playerclass"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)


class PlayerRace(db.Model):
    __tablename__ = "playerrace"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)


def init_defaults():
    """pre-populate action options table"""
    if ActionOption.query.first() is None:
        action_options = [
            {"name": "rest"},
            {"name": "inspect"},
            {"name": "fight"},
            {"name": "quit"},
        ]
        for act_opt in action_options:
            current_act_opt = ActionOption()
            current_act_opt.name = act_opt["name"]
            db.session.add(current_act_opt)
        db.session.commit()
    if TileTypeOption.query.first() is None:
        tile_types = [
            {"name": "scene"},
            {"name": "monster"},
            {"name": "sign"},
            {"name": "treasure"},
        ]
        for tile_type in tile_types:
            current_tile_type = TileTypeOption()
            current_tile_type.name = tile_type["name"]
            db.session.add(current_tile_type)
        db.session.commit()
    if PlayerClass.query.first() is None:
        tile_types = [{"name": "witch"}, {"name": "fighter"}, {"name": "healer"}]
        for tile_type in tile_types:
            current_tile_type = PlayerClass()
            current_tile_type.name = tile_type["name"]
            db.session.add(current_tile_type)
        db.session.commit()
    if PlayerRace.query.first() is None:
        tile_types = [{"name": "Human"}, {"name": "Elf"}, {"name": "Pandarian"}]
        for tile_type in tile_types:
            current_tile_type = PlayerRace()
            current_tile_type.name = tile_type["name"]
            db.session.add(current_tile_type)
        db.session.commit()


def user_exists(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return True
    else:
        return False
