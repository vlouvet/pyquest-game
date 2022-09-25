from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField
from wtforms.validators import DataRequired

class CharacterForm(FlaskForm):
    name = StringField('Character Name', validators=[DataRequired()])
    charclass = SelectField(u'Character Class', coerce=int, validators=[DataRequired()])
    charrace = SelectField(u'Character Race', coerce=int, validators=[DataRequired()])

class UserNameForm(FlaskForm):
    username = StringField('User Email Address:', validators=[DataRequired()])

class TileForm(FlaskForm):
    type = StringField(u'Tile Type', render_kw={'readonly':True})
    tilecontent = TextAreaField(u'content', render_kw={'readonly':True})
    tileaction = SelectField(u'Tile Action', coerce=int, validators=[DataRequired()])