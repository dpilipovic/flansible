""" Main app file """
import os
import datetime
from datetime import timedelta
import logging
import logging.handlers
import yaml

import flask
from flask import app, session, Blueprint
from flask_bootstrap import Bootstrap
from flask_ldap3_login import LDAP3LoginManager
from flask_login import LoginManager, UserMixin
# API stuff added
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from app.conf.config import APP_PATH, LOG_FILE

app = flask.Flask(__name__)
Bootstrap(app)
app.config.from_object('app.conf.config')

# Setup logging
logging.basicConfig(filename=(f'{APP_PATH}logs/{LOG_FILE}'), level=logging.INFO)
formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler = logging.handlers.WatchedFileHandler(f'{APP_PATH}logs/{LOG_FILE}')
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
app.logger.addHandler(handler)
# API
api = Api(app, prefix="/api/v1")
# This is needed in order for error handlers to work properly in Flask restfull
app.config['PROPAGATE_EXCEPTIONS'] = True
#
""" Import database which was created in createdb.py """
from app.database.createdb import db
from app.database.models import User

""" LDAP stuff """
login_manager = LoginManager(app)              # Setup a Flask-Login Manager
ldap_manager = LDAP3LoginManager(app)          # Setup a LDAP3 Login Manager.


""" Declare a User Loader for Flask-Login. Simply returns the User if it exists in our 'database', otherwise returns None."""
@login_manager.user_loader
def load_user(dn):
    return User.query.filter_by(dn=dn).first()

""" Redirect unauthorized calls back to login page rather then giving them a 401 error """
@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect('/login')

""" Declare The User Saver for Flask-Ldap3-Login This method is called whenever a LDAPLoginForm() successfully validates.
Here you have to save the user, and return it so it can be used in the login controller. """
@ldap_manager.save_user
def save_user(dn, username, data, memberships):
    id = int(data.get("objectSid").split('-')[-1])
    if app.config['LOGIN_GROUP_FULL_DN'] in data.get("memberOf"):
        user = User.query.filter_by(id=id).first()
        if not user:
            user = User(
                id=id,
                dn=dn,
                username=username,
                email=data['mail'],
                firstname=data['givenName'],
                lastname=data['sn']
            )
            db.session.add(user)
            db.session.commit()
        return user

""" is_safe_url function is needed by Flask-Login to make sure that login redirect is not sent to a malicious site """
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

""" Load config from buttons.yml into a list of dictionaries called buttons , exit application if file is not a valid yaml: """
yaml_file = os.path.join(app.config['APP_PATH'] + 'conf' + '/buttons.yml')
try:
    buttons = yaml.safe_load(open(yaml_file, 'r'))
    required = ['button_name', 'button_description', '_cmd', '_id']
    """ Validate that we have all 4 required parameters in each dictionary in the list, exit application if any parameter is missing. """
    for i in required:
        if all(i in b for b in buttons) == False:
            app.logger.critical('ERROR: missing required parameter: %s in %s. Required parameters are: button_name, button_description, _cmd and _id. Optional parameter is: api.', i, yaml_file)
            print('ERROR: missing required parameter: {} in {}. Required parameters are: button_name, button_description, _cmd and _id. Optional parameter is: api.'.format(i, yaml_file))
            os._exit(0)
    app.logger.info('Application started up, yaml file validated and loaded succesfully.')
except Exception as e:
    print(e)
    app.logger.critical('ERROR: exiting application due to error: %s', str(e))
    os._exit(0)

""" Global function that allows streaming with context used in order to render results of playbook line by line live, used by /run view function. """
def stream_template(template_name, **context):
    app.update_template_context(context)
    t = app.jinja_env.get_template(template_name)
    rv = t.stream(context)
    rv.disable_buffering()
    return rv

""" Expire sessions after an hour """
@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=60)

""" Import and register Blueprints. """
from app.ui.views import ui_blueprint
from app.admin.views import admin_blueprint
from app.restapi.views import restapi_blueprint

app.register_blueprint(ui_blueprint)
app.register_blueprint(admin_blueprint, url_prefix='/admin')
app.register_blueprint(restapi_blueprint)
