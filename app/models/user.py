import os
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('users.id'))
)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    meals = db.relationship('Meal', back_populates='user', lazy='dynamic')
    refresh_token = db.Column(db.String(128), unique=True)
    refresh_token_expiration = db.Column(db.DateTime)
    
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_refresh_token(self):
        self.refresh_token = os.urandom(32).hex()
        self.refresh_token_expiration = datetime.now(timezone.utc) + timedelta(days=30)
        return self.refresh_token

    def revoke_refresh_token(self):
        self.refresh_token = None
        self.refresh_token_expiration = None

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def __repr__(self):
        return f'<User {self.username}>'
