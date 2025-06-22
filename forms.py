from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, NumberRange, EqualTo
from models import User, Group

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), 
        Length(min=3, max=20, message='Username must be between 3 and 20 characters')
    ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(), 
        Length(min=6, message='Password must be at least 6 characters')
    ])
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(), 
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValueError('Username already exists. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValueError('Email already registered. Please use a different email.')

class CreateGroupForm(FlaskForm):
    name = StringField('Group Name', validators=[
        DataRequired(), 
        Length(min=3, max=50, message='Group name must be between 3 and 50 characters')
    ])
    description = TextAreaField('Description', validators=[
        Length(max=200, message='Description cannot exceed 200 characters')
    ])
    max_members = IntegerField('Maximum Members', validators=[
        DataRequired(), 
        NumberRange(min=2, max=15, message='Group must have between 2 and 15 members')
    ], default=10)
    submit = SubmitField('Create Group')

class JoinGroupForm(FlaskForm):
    invite_code = StringField('Invite Code', validators=[
        DataRequired(), 
        Length(min=8, max=8, message='Invite code must be 8 characters')
    ])
    submit = SubmitField('Join Group')
    
    def validate_invite_code(self, invite_code):
        group = Group.query.filter_by(invite_code=invite_code.data).first()
        if not group:
            raise ValueError('Invalid invite code.')

class AddBookForm(FlaskForm):
    title = StringField('Book Title', validators=[
        DataRequired(), 
        Length(min=1, max=200, message='Title cannot exceed 200 characters')
    ])
    author = StringField('Author', validators=[
        DataRequired(), 
        Length(min=1, max=100, message='Author name cannot exceed 100 characters')
    ])
    page_count = IntegerField('Number of Pages', validators=[
        DataRequired(), 
        NumberRange(min=1, max=10000, message='Page count must be between 1 and 10,000')
    ])
    status = SelectField('Status', choices=[
        ('To Read', 'To Read'),
        ('Reading', 'Currently Reading'),
        ('Read', 'Finished Reading')
    ], default='To Read')
    submit = SubmitField('Add Book')


#  Replaced addbook form with a search form for Google Books API integration
class BookSearchForm(FlaskForm):
    query = StringField('Search for a book by title or author', validators=[DataRequired()])
    submit = SubmitField('Search')