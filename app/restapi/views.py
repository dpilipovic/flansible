""" All flask routes/views defined in here. """
import logging
import random

from flask import render_template, flash, request, Blueprint
from flask_login import current_user, login_required
# API stuff added
from flask_jwt import JWT
# Needed to auto-generate password hash it and salt it
from werkzeug.security import generate_password_hash

# Import API Classes/Resources from resources.py and map them to routes here.
from app.restapi.resources import AllIDs, RetrieveIDs, ExecIDs
from app import app, api, buttons, db
# Import Class/DB tables from Models
from app.database.models import Apiusers
# This needs to be imported after the database is initialized and table created
from app.restapi.secure_check import authenticate, identity
jwt = JWT(app, authenticate, identity)

log = logging.getLogger('app')

restapi_blueprint = Blueprint('restapi', __name__, template_folder='templates/restapi')

@restapi_blueprint.route('/register', methods=['GET', 'POST'])
@login_required
def register_api():
    company_info = app.config['COMPANY_INFO']
    return render_template("register.html", company_info=company_info)

@restapi_blueprint.route('/regresult', methods=['GET', 'POST'])
@login_required
def regresult():
    company_info = app.config['COMPANY_INFO']
    app_url = app.config['APP_URL']
    api_endpoints = [b['_id'] for b in buttons if 'api' in b]
    if request.method == 'GET':
        return render_template("register.html", company_info=company_info)
    if request.method == 'POST':
        _user = request.form['username']
        _email = request.form['emails']
        if request.form.get('notify'):
            _notify = 1
        else:
            _notify = 0
        # Here we validate a few things, whether user already exists and whether ldap_user has maximum users already configured.
        exists = Apiusers.query.filter(Apiusers.username == _user).first()
        user_count = Apiusers.query.filter_by(ldap_user=str(current_user).split(',')[0][3:]).count()
        if exists:
            flash('Username is already in use %s' % _user, 'danger')
            app.logger.error('Username is already in use %s' % _user)
            return render_template("register.html", company_info=company_info)
        elif user_count >= int(app.config['MAX_APIUSERS']):
            flash('User %s has already registered maximum number of allowed API users.' % str(current_user).split(',')[0][3:], 'danger')
            app.logger.error('User %s has already registered maximum number of allowed API users.' % str(current_user).split(',')[0][3:])
            return render_template("register.html", company_info=company_info)
        else:
            password = (''.join([random.choice(list('123456789qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM'))for x in range(8)]))
            _password_hash = generate_password_hash(password)
            _ldap_user = str(current_user).split(',')[0][3:]
        try:
            record = Apiusers(username=_user, email=_email, notify=_notify, password_hash=_password_hash, ldap_user=_ldap_user)
            db.session.add(record)
            db.session.commit()
            app.logger.info('Created new API user: %s with email address %s and notification set to %s. It belongs to User: %s', _user, _email, bool(_notify), str(current_user).split(',')[0][3:])
        except Exception as e:
            app.logger.error('ERROR: %s ', str(e))
            flash('{}'.format(str(e)), 'danger')
            return render_template("register.html", company_info=company_info)
    return render_template("regresult.html", password=password, _user=_user, api_endpoints=api_endpoints, company_info=company_info, app_url=app_url)

@restapi_blueprint.route('/user_reset', methods=['POST'])
@login_required
def user_reset():
    company_info = app.config['COMPANY_INFO']
    app_url = app.config['APP_URL']
    api_endpoints = [b['_id'] for b in buttons if 'api' in b]
    _user = request.form['username']
    _ldap_user = str(current_user).split(',')[0][3:]
    item = Apiusers.query.filter_by(username=_user, ldap_user=_ldap_user).all()
    if not item:
        flash("API user %s doesn't exist, or doesn't belong to you." % _user, 'danger')
        app.logger.error("Invalid user reset password attempt. API user %s doesn't exist, or doesn't belong to %s", _user, _ldap_user)
        return render_template("register.html", company_info=company_info)
    else:
        try:
            password = (''.join([random.choice(list('123456789qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM'))for x in range(8)]))
            _password_hash = generate_password_hash(password)
            for i in item:
                i.password_hash = _password_hash
            db.session.commit()
            app.logger.info('%s has reset a password for API user %s!', _ldap_user, _user)
            flash('API user: %s password has been reset!' % _user, 'info')
            return render_template("regresult.html", password=password, _user=_user, api_endpoints=api_endpoints, company_info=company_info, app_url=app_url)
        except Exception as e:
            db.session.rollback()
            app.logger.error('ERROR: %s ', str(e))
            flash('{}'.format(str(e)), 'danger')
            return render_template("register.html", company_info=company_info)

# API views
api.add_resource(AllIDs, '/list', methods=['GET'])

api.add_resource(RetrieveIDs, '/<string:id>', methods=['GET'])

api.add_resource(ExecIDs, '/<string:id>', methods=['POST'])
