import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField, FloatField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length, Optional, NumberRange
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username or Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class UserRegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register as Donor')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

    def validate_phone_number(self, phone_number):
        user = User.query.filter_by(phone_number=phone_number.data).first()
        if user is not None:
            raise ValidationError('This phone number is already in use.')

class HomeAdminRegistrationForm(FlaskForm):
    # Admin details
    username = StringField('Your Username', validators=[DataRequired()])
    email = StringField('Your Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Your Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])

    # Home details
    home_name = StringField('Home Name', validators=[DataRequired()])
    home_address = TextAreaField('Home Address', validators=[DataRequired()])
    home_description = TextAreaField('Home Description')
    home_occupant_count = IntegerField('Number of Occupants', validators=[DataRequired()])
    home_contact_phone = StringField('Home Public Contact Number', validators=[DataRequired(), Length(min=10, max=15)])
    home_payment_details = StringField('Home UPI ID / Payment Details')

    submit = SubmitField('Register and Add Home')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('This username is already taken.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('This email address is already in use.')

    def validate_phone_number(self, phone_number):
        user = User.query.filter_by(phone_number=phone_number.data).first()
        if user is not None:
            raise ValidationError('This phone number is already in use.')

    def validate_home_payment_details(self, field):
        if field.data:
            if not re.match(r'^[\w\.\-]+@[\w\.\-]+$', field.data):
                raise ValidationError('Invalid UPI ID format. Format should be username@bank.')

class HomeUpdateForm(FlaskForm):
    occupant_count = IntegerField('Number of Occupants', validators=[DataRequired()])
    contact_phone = StringField('Home Public Contact Number', validators=[DataRequired(), Length(min=10, max=15)])
    payment_details = StringField('Home UPI ID / Payment Details')
    description = TextAreaField('Home Description')

    req_grocery = TextAreaField('Grocery / Food Requirements')
    req_clothes = TextAreaField('Clothing Requirements')
    req_stationary = TextAreaField('Stationary Requirements')
    req_medical = TextAreaField('Medical Assistance Requirements')
    
    submit = SubmitField('Update Details')

    def validate_payment_details(self, field):
        if field.data:
            if not re.match(r'^[\w\.\-]+@[\w\.\-]+$', field.data):
                raise ValidationError('Invalid UPI ID format. Format should be username@bank.')

class MoneyDonationForm(FlaskForm):
    amount = FloatField('Amount (₹)', validators=[DataRequired(message="Please enter the amount."), NumberRange(min=1, message="Amount must be at least ₹1.")])
    transaction_id = StringField('UPI Transaction ID', validators=[DataRequired(message="Please enter the UPI Transaction ID."), Length(max=100)])
    description = TextAreaField('Message (Optional)', validators=[Optional(), Length(max=200)])
    home_id = IntegerField('Home ID', validators=[DataRequired()])
    submit = SubmitField('Confirm Payment')
    
    # Hidden fields to store Razorpay response data
    razorpay_payment_id = StringField('Payment ID')
    razorpay_order_id = StringField('Order ID')
    razorpay_signature = StringField('Signature')
    
    submit = SubmitField('Pay Now')

class InKindDonationForm(FlaskForm):
    description = TextAreaField('Items Donated', validators=[DataRequired(message="Please list the items you are donating."), Length(min=1, max=200)])
    home_id = IntegerField('Home ID', validators=[DataRequired()])
    submit = SubmitField('Record Items')

class VolunteerOpportunityForm(FlaskForm):
    title = StringField('Opportunity Title', validators=[DataRequired(), Length(max=140)])
    description = TextAreaField('Detailed Description', validators=[DataRequired()])
    skills_required = StringField('Skills Required (comma-separated)', validators=[DataRequired(), Length(max=200)])
    time_commitment = StringField('Time Commitment (e.g., 2 hours/week)', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Post Opportunity')