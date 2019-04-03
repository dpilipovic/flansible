"""Database Models - Tables defined as Classes"""
import re
from datetime import datetime
from sqlalchemy.orm import validates
from flask_login import UserMixin
from app.database.createdb import db

#############################################################
###  MODELS #####
#############################################################
class Apiusers(db.Model):
    """ Table that contains API users """
    __tablename__ = 'apiusers'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, nullable=False)
    password_hash = db.Column(db.String(128))
    notify = db.Column(db.Boolean(), nullable=False, default=False)
    ldap_user = db.Column(db.String(64))
    created = db.Column(db.DateTime(), default=datetime.utcnow)
    updated = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)


    def __repr__(self):
        return self.username

    # https://nunie123.github.io/sqlalchemy-validation.html
    @validates('username')
    def validate_username(self, key, username):
        if not username:
            raise ValueError('No username provided')

        # This blocks making any updates on existing usernames in table so it will have to move to the registerresult view instead
        # if Apiusers.query.filter(Apiusers.username == username).first():
        #   raise ValueError('Username is already in use %s' % username)

        if len(username) < 5 or len(username) > 20:
            raise ValueError('Username must be between 5 and 20 characters')

        # This also blocks updating the user in admin view if ldap user has max users, so it was moved to registerresult view instead
        # Check whether user has already registered maximum number of API users allowed
        #if Apiusers.query.filter_by(ldap_user=str(current_user).split(',')[0][3:]).count() >= int(MAX_APIUSERS):
        #  raise ValueError('User %s has already registered maximum number of allowed API users.' % str(current_user).split(',')[0][3:])

        return username

    @validates('email')
    def validate_email(self, key, email):
        if not email:
            raise ValueError('No email provided')

        # Simple email validation
        #if not re.match("[^@]+@[^@]+\.[^@]+", email):
        # Most correct regex which we use with JQuery as well on another place in this project
        if not re.match(r"^((([a-z]|\d|[!#\$%&'\*\+\-\/=\?\^_`{\|}~]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])+(\.([a-z]|\d|[!#\$%&'\*\+\-\/=\?\^_`{\|}~]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])+)*)|((\x22)((((\x20|\x09)*(\x0d\x0a))?(\x20|\x09)+)?(([\x01-\x08\x0b\x0c\x0e-\x1f\x7f]|\x21|[\x23-\x5b]|[\x5d-\x7e]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(\\([\x01-\x09\x0b\x0c\x0d-\x7f]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]))))*(((\x20|\x09)*(\x0d\x0a))?(\x20|\x09)+)?(\x22)))@((([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.)+(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.?$", email):
            raise ValueError('Provided email is not an email address')

        return email


class Adminusers(db.Model):
    """ Table that contains Admin user """
    __tablename__ = 'adminusers'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created = db.Column(db.DateTime(), default=datetime.utcnow)
    updated = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return self.username


class Runhistory(db.Model):
    """ Table that contains history of runs """
    __tablename__ = 'runhistory'
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(64), index=True, nullable=False)
    type = db.Column(db.String(64), nullable=False)
    time_started = db.Column(db.DateTime(), default=datetime.utcnow)
    time_completed = db.Column(db.DateTime(), onupdate=datetime.utcnow)
    status = db.Column(db.String(64), nullable=False)
    logfile = db.Column(db.String(64), nullable=False)

    def __repr__(self):
        return self.logfile


# Declare an Object Model for the user, and make it comply with the
# flask-login UserMixin mixin.
class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    dn = db.Column(db.String(255), unique=True)
    username = db.Column(db.String(255))
    email = db.Column(db.String(255))
    firstname = db.Column(db.String(255))
    lastname = db.Column(db.String(255))

    def __repr__(self):
        return self.dn

    def get_id(self):
        return self.dn
