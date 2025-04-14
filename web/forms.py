from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, TextAreaField, FileField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo



class RegistrationForm(FlaskForm):
    phone_number = StringField("Phone Number", validators=[DataRequired(), Length(min=11, max=11)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo('password', message="Passwords must match.")])


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])