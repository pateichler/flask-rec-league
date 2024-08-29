from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import (
    DataRequired, Length, Email, EqualTo, ValidationError
)
from sqlalchemy import func

from recLeague.models import User


class RegistrationForm(FlaskForm):
    """Form for registering a new user.
    
    Attributes:
        first_name: 
        last_name: 
        email: 
        password: 
        confirm_password: 
        league_password: 
        submit: 
    """
    first_name = StringField(
        'First name', validators=[DataRequired(), Length(min=2, max=15)]
    )
    last_name = StringField(
        'Last name', validators=[DataRequired(), Length(min=1, max=15)]
    )
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField(
        'Confirm Password', validators=[DataRequired(), EqualTo('password')]
    )
    league_password = PasswordField(
        'League password', validators=[DataRequired()]
    )
    submit = SubmitField('Sign Up')

    def validate_first_name(self, name):
        if name.data.lower() == "guest":
            raise ValidationError('Name can not be guest')

    def validate_email(self, email):
        user = User.query.filter(
            func.lower(User.email) == func.lower(email.data)
        ).first()
        if user:
            raise ValidationError('That email is already registered. \
                Please use a different one.')


class LoginForm(FlaskForm):
    """Form for logging in user.
    
    Attributes:
        email: 
        password: 
        remember: 
        submit: 
    """
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

    def validate_email(self, email):
        # Only check valid email if not admin
        if email.data != "admin":
            e = Email()
            e(self, email)


class RequestResetForm(FlaskForm):
    """Form for requesting a reset password.
    
    Attributes:
        email: 
        submit: 
    """
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter(
            func.lower(User.email) == func.lower(email.data)
        ).first()
        if user is None:
            raise ValidationError('There is no account with that email. \
                You must register first.')


class ResetPasswordForm(FlaskForm):
    """Form for resetting a password.
    
    Form is used only once a password reset token is verified.
    
    Attributes:
        password: Field for new password to set user.
        confirm_password: Field for repeat of new password.
        submit: 
    """
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField(
        'Confirm Password', validators=[DataRequired(), EqualTo('password')]
    )
    submit = SubmitField('Reset Password')
