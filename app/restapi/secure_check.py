"""Secure_check module functions handle validation of users to which JWT
   token can be issued against the database table Apiusers"""
from werkzeug.security import check_password_hash
from app.database.models import Apiusers


def authenticate(username, password):
    apiusers = Apiusers.query.all()
    username_table = {u.username: u for u in apiusers}
    user = username_table.get(username, None)
    if user and check_password_hash(user.password_hash, password) == True:
        return user
    else:
        return None

def identity(payload):
    apiusers = Apiusers.query.all()
    userid_table = {u.id: u for u in apiusers}
    user_id = payload['identity']
    return userid_table.get(user_id, None)
