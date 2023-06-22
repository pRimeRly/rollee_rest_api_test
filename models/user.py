from db import db
from sqlalchemy import JSON


class UserModel(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    user_data = db.Column(JSON, nullable=False)
    token = db.Column(db.String, nullable=False)
