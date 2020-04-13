from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from hashlib import md5

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, index=True, unique=True)
    password_hash = db.Column(db.String)
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'{self.id}, {self.email}'

class Post(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(80), unique = True)
    description = db.Column(db.String(140))
    body = db.Column(db.String)
    timestamp = db.Column(db.DateTime, default = datetime.utcnow)
    comments = db.relationship('Comment', backref='comments', lazy='dynamic')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'{self.id}, {self.title}, {self.description}, {self.body}, {self.timestamp}'

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64))
    name = db.Column(db.String)
    comment = db.Column(db.String)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def __repr__(self):
        return f'{self.id}, {self.email}, {self.name}, {self.comment}, {self.timestamp}'

class Stats(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    comments = db.Column(db.Integer, default = 0)
    day_comments = db.Column(db.Date, default = date.today)
    visits = db.Column(db.Integer, default = 1)
    day_visits = db.Column(db.Date, default = date.today)
    shares = db.Column(db.Integer, default = 0)
    day_shares = db.Column(db.Date, default = date.today)

    def __repr__(self):
        return f'{self.id}, {self.comments}, {self.day_comments}, {self.visits}, \
            {self.day_visits}, {self.shares}, {self.day_shares}'

@login.user_loader
def load_user(id):
    return User.query.get(id)
