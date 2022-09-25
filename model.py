from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String)
    current_tile =  db.Column(db.String, nullable=True)
    hitpoints = db.column(db.Integer)
    playerclass =  db.Column(db.Integer, db.ForeignKey('playerclass.id'))
    playerrace =  db.Column(db.Integer, db.ForeignKey('playerrace.id'))

class Tile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Integer, db.ForeignKey('tiletypeoption.id'))
    action = db.relationship("Action")
    valid = db.Column(db.Boolean)

class Action(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    tile = db.Column(db.Integer, db.ForeignKey('tile.id'))

class ActionOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

class TileTypeOption(db.Model):
    __tablename__ = "tiletypeoption"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

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
        action_options = [{"name":"rest"}, {"name":"inspect"}, {"name":"fight"}, {"name":"quit"}]
        for act_opt in action_options:
            current_act_opt = ActionOption(name=act_opt['name'])
            db.session.add(current_act_opt)
        db.session.commit()
    if TileTypeOption.query.first() is None:
        tile_types = [{"name":"scene"}, {"name":"monster"}, {"name":"sign"}, {"name":"treasure"}]
        for tile_type in tile_types:
            current_tile_type = TileTypeOption(name = tile_type['name'])
            db.session.add(current_tile_type)
        db.session.commit()
    if PlayerClass.query.first() is None:
        tile_types = [{"name":"witch"}, {"name":"fighter"}, {"name":"healer"}]
        for tile_type in tile_types:
            current_tile_type = PlayerClass(name = tile_type['name'])
            db.session.add(current_tile_type)
        db.session.commit()
    if PlayerRace.query.first() is None:
        tile_types = [{"name":"Human"}, {"name":"Elf"}, {"name":"Pandarian"}]
        for tile_type in tile_types:
            current_tile_type = PlayerRace(name = tile_type['name'])
            db.session.add(current_tile_type)
        db.session.commit()