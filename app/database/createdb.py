""" Create Database object here """
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app import app
from app.conf.config import SQLALCHEMY_TRACK_MODIFICATIONS

# DB SETUP:
with app.app_context():
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+os.path.join(basedir, 'data.sqlite')
    #app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db = SQLAlchemy(app)
    Migrate(app, db)
    # Create all tables
    db.create_all()
