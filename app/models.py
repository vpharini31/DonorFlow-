from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

# Association table for User and Reward
redeemed_rewards = db.Table('redeemed_rewards',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('reward_id', db.Integer, db.ForeignKey('reward.id'), primary_key=True),
    db.Column('redeemed_on', db.DateTime, default=datetime.utcnow)
)

# Association table for User and VolunteerOpportunity
volunteer_applications = db.Table('volunteer_applications',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('opportunity_id', db.Integer, db.ForeignKey('volunteer_opportunity.id'), primary_key=True),
    db.Column('applied_on', db.DateTime, default=datetime.utcnow),
    db.Column('status', db.String(20), default='pending') # pending, accepted, rejected
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    phone_number = db.Column(db.String(20), unique=True)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), index=True)  # 'donor' or 'home_admin'
    points = db.Column(db.Integer, default=0)

    # For home_admin, this links to the home they manage
    home = db.relationship('Home', back_populates='admin', uselist=False, foreign_keys='Home.admin_id')

    # Relationship for redeemed rewards
    redeemed = db.relationship('Reward', secondary=redeemed_rewards, lazy='subquery',
                               backref=db.backref('redeemers', lazy=True))
    
    # Relationship for volunteer applications
    applied_opportunities = db.relationship('VolunteerOpportunity', secondary=volunteer_applications, lazy='subquery',
                                            backref=db.backref('applicants', lazy=True))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Home(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), unique=True)
    address = db.Column(db.String(200))
    description = db.Column(db.Text)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    occupant_count = db.Column(db.Integer)
    contact_phone = db.Column(db.String(20))
    payment_details = db.Column(db.String(100)) # For UPI ID
    is_verified = db.Column(db.Boolean, default=False)
    
    # Requirements
    req_grocery = db.Column(db.Text)
    req_clothes = db.Column(db.Text)
    req_stationary = db.Column(db.Text)
    req_medical = db.Column(db.Text)

    # Link to the admin user
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    admin = db.relationship('User', back_populates='home', foreign_keys=[admin_id])

    def __repr__(self):
        return f'<Home {self.name}>'

class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    donor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    home_id = db.Column(db.Integer, db.ForeignKey('home.id'))
    confirmed = db.Column(db.Boolean, default=False)
    confirmed_on = db.Column(db.DateTime, nullable=True)
    thank_you_message = db.Column(db.Text, nullable=True)
    amount = db.Column(db.Float, nullable=True)
    transaction_id = db.Column(db.String(100), nullable=True)

    donor = db.relationship('User', backref='donations')
    home = db.relationship('Home', backref='donations')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    link = db.Column(db.String(255)) # Optional link for the notification

    user = db.relationship('User', backref='notifications')

    def __repr__(self):
        return f'<Notification {self.message}>'

class Reward(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    description = db.Column(db.String(200))
    points_cost = db.Column(db.Integer)
    icon = db.Column(db.String(50)) # For a Bootstrap icon class e.g., 'bi-star-fill'

class VolunteerOpportunity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140))
    description = db.Column(db.Text)
    skills_required = db.Column(db.String(200))
    time_commitment = db.Column(db.String(100))
    status = db.Column(db.String(20), default='open', index=True) # open, closed
    posted_on = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    
    home_id = db.Column(db.Integer, db.ForeignKey('home.id'))
    home = db.relationship('Home', backref='volunteer_opportunities')

    def __repr__(self):
        return f'<VolunteerOpportunity {self.title}>'