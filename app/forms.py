from starlette_wtf import StarletteForm
from wtforms import TextAreaField, PasswordField, StringField, DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from wtforms.widgets import PasswordInput


class RegistrationForm(StarletteForm):
    phone_number = StringField("Phone Number", validators=[DataRequired(), Length(min=11, max=11)])
    full_name = StringField("Full Name", validators=[DataRequired(), Length(min=1, max=40)])
    birth_date = DateField("Birth Date", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired()])


class LoginForm(StarletteForm):
    phone_number = StringField("Phone Number", validators=[DataRequired(), Length(min=11, max=11)])
    password = PasswordField("Password", validators=[DataRequired()])


class RequestPhoneCodeForm(StarletteForm):
    pass


class TripForm(StarletteForm):
    pass


class ChangeUserInfoForm(StarletteForm):
    pass


class ResetPasswordRequestForm(StarletteForm):
    pass


class ResetPasswordForm(StarletteForm):
    pass