from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired

class CharacterForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    charclass = StringField('class', validators=[DataRequired()])
    race = StringField('race', validators=[DataRequired()])

class NameForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])

class TileForm(FlaskForm):
    type = StringField('type', validators=[DataRequired()])
    tilecontent = StringField('content', validators=[DataRequired()])
    #TODO: extend tile form to include more details