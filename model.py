from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String)
    current_tile =  db.Column(db.String, nullable=True)

class Tile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String)