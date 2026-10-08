from flask import session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models import User
from app.ui_translations import UI_TRANSLATIONS

class LoginForm(FlaskForm):
    """Form for existing users to sign in."""
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required."),
        Email(message="Please enter a valid email address.")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required.")
    ])
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    """Form for new users to register."""
    name = StringField('Full Name', validators=[
        DataRequired(message="Name is required."),
        Length(min=2, max=100, message="Name must be between 2 and 100 characters.")
    ])
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required."),
        Email(message="Please enter a valid email address.")
    ])
    role = SelectField('Role', choices=[
        ('student', 'Student / Researcher'),
        ('doctor', 'Doctor / Clinician')
    ], validators=[DataRequired()])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required."),
        Length(min=6, message="Password must be at least 6 characters long.")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password."),
        EqualTo('password', message="Passwords must match.")
    ])
    submit = SubmitField('Create Account')

    def validate_email(self, email):
        """Validate that email is not already taken."""
        user = User.query.filter_by(email=email.data.strip().lower()).first()
        if user:
            message = 'An account with this email address already exists. Please log in instead.'
            if session.get('language') == 'hi':
                message = UI_TRANSLATIONS[message]
            raise ValidationError(message)
