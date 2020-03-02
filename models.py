# models.py

from flask_login import UserMixin
from . import db
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    rlModel = db.relationship('Model', backref='user', lazy=True)
    rlLog = db.relationship('Log', backref='user', lazy=True)


class Model(db.Model,Base):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    num_train_date = db.Column(db.Integer, nullable=False)
    num_test_date = db.Column(db.Integer, nullable=False)
    gamma = db.Column(db.Float)
    epsilon = db.Column(db.Float)
    epsilon_min = db.Column(db.Float)
    epsilon_decay = db.Column(db.Float)
    episode_count = db.Column(db.Integer)
    model_name = db.Column(db.String(100), nullable=False)
    currency_symobol = db.Column(db.String(20), nullable=False)
    start_balance = db.Column(db.Integer)
    currency_amount = db.Column(db.Float)
    avg_currency_rate = db.Column(db.Float)
    log_id = db.Column(db.Integer, db.ForeignKey('log.id'))
    log = db.relationship("Log")

class Log(db.Model,Base):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime)
    log_text = db.Column(db.String(1000))
