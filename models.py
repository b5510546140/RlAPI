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
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
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
    policy = db.relationship('Policy', backref='model', lazy=True)
    model_path = db.Column(db.String(100), nullable=False)
    have_model = db.Column(db.Boolean)
    buy_lot_size = db.Column(db.Float)
    sale_lot_size = db.Column(db.Float)

class Log(db.Model,Base):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime)
    log_text = db.Column(db.String(1000))
    train_text = db.Column(db.String(1000))
    test_text = db.Column(db.String(1000))

class Policy(db.Model,Base):
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'), nullable=False)
    created_at = db.Column(db.DateTime)
    action = db.Column(db.String(10))
    con = db.Column(db.String(3))
    sym = db.Column(db.String(15))
    num = db.Column(db.Integer)
