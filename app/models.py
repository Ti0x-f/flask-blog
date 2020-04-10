from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, index=True, unique=True)
    password_hash = db.Column(db.String)
