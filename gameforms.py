from flask_wtf import FlaskForm
from wtforms import StringField, SelectField
from wtforms.validators import DataRequired

class CharacterForm(FlaskForm):
    name = StringField('Character Name', validators=[DataRequired()])
    charclass = SelectField(u'Character Class', coerce=int, validators=[DataRequired()])
    charrace = SelectField(u'Character Race', coerce=int, validators=[DataRequired()])

class UserNameForm(FlaskForm):
    username = StringField('User Email Address:', validators=[DataRequired()])

class TileForm(FlaskForm):
    type = SelectField(u'Tile Type', coerce=int)
    tilecontent = StringField('content')
    tileaction = SelectField(u'Tile Action', coerce=int, validators=[DataRequired()])