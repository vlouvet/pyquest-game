from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SelectField,
    TextAreaField,
    PasswordField,
    SubmitField,
    BooleanField,
)
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from . import model  # Import the model module


class CharacterForm(FlaskForm):
    name = StringField("Character Name", validators=[DataRequired()])
    charclass = SelectField("Character Class", coerce=int, validators=[DataRequired()])
    charrace = SelectField("Character Race", coerce=int, validators=[DataRequired()])


class UserNameForm(FlaskForm):
    username = StringField("User Email Address:", validators=[DataRequired()])


class TileForm(FlaskForm):
    tileid = StringField("Tile ID", render_kw={"readonly": True})
    type = StringField("Tile Type", render_kw={"readonly": True})
    content = TextAreaField("content", render_kw={"readonly": True})
    action = SelectField("Tile Action", coerce=int, validators=[DataRequired()])


class RegisterForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=2, max=20)]
    )
    password = PasswordField("Password", validators=[DataRequired()])
    confirm = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Sign Up")

    def validate_username(self, username):
        user = model.User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(
                "That username is taken. Please choose a different one."
            )


class LoginForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=2, max=20)]
    )
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login")
