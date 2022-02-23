from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired

class CharacterForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    charclass = StringField('class', validators=[DataRequired()])
    race = StringField('race', validators=[DataRequired()])

class NameForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])    