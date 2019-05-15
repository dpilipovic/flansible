""" All flask UI routes/views defined in here. """
import os
import datetime
from datetime import timedelta
import logging
import tzlocal

from flask import render_template, flash, redirect, request, url_for, session, Response, stream_with_context, send_from_directory, Blueprint
from flask_login import login_user, current_user, logout_user, login_required
from flask_ldap3_login.forms import LDAPLoginForm

from app import app, buttons, stream_template, is_safe_url
from app.ui.mailer_ui import send_email_ui
# Import Class/DB tables from Models
from app.database.models import Runhistory
# This needs to be imported after the database is initialized and table created
from app.ui.connect_ssh_ui import test_ssh, run_ssh_ui

log = logging.getLogger('app')
#default = Blueprint('default', __name__, template_folder = 'templates/ui')
ui_blueprint = Blueprint('ui', __name__, template_folder='templates/ui')


# Declare ROUTES

@ui_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    # Instantiate a LDAPLoginForm which has a validator to check if the user exists in LDAP.
    form = LDAPLoginForm(request.form)
    if request.method == 'GET':
        return render_template('login.html', form=form)
    else:
      if form.validate_on_submit():
          if form.user:
              login_user(form.user)
              # Successfully logged in, We can now access the saved user object via form.user.
              name = str(form.user).split(',')[0][3:]
              app.logger.info('%s succesfully logged in!', name) # Log who logged in
              next = request.args.get('next')
              # is_safe_url from __init__.py should check if the url is safe for redirects.
              # See http://flask.pocoo.org/snippets/62/ for an example.
              if not is_safe_url(next):
                return flask.abort(400)
              return redirect(next or url_for('ui.index'))  # Send them home
          else:
              error = True
              name = str(form.username.data)
              app.logger.warn('Invalid login attempt by user: %s !', name)
              return render_template('login.html', form=form, error=error)
      else:
          name = str(form.username.data)
          app.logger.warn('Invalid login attempt by user: %s', name)
          return render_template('login.html', form=form)

@ui_blueprint.route('/', methods=['GET', 'POST'])
def index():
    if not current_user or current_user.is_anonymous:
        return redirect(url_for('ui.login'))
        # User is logged in so we can load home page in all it's beauty!
    return render_template("index.html", buttons=buttons)

@ui_blueprint.route('/run', methods=['GET', 'POST'])
@login_required
def run():
    # Here we search for passed values from each of the buttons configured in buttons.yml and assign ansible playbooks that correspond to them.
    if request.method == 'POST':
        id = request.form['pass_value']
        cmd = None
        for btn in buttons:
            if btn['_id'] == id:
                cmd = (btn['_cmd'])
        if cmd == None:
        # How did we get here? This is just in case user calls /run manually
            return redirect('/')

        try:
            test_ssh(cmd)
        except ValueError as e:
            app.logger.error('ERROR: %s ', str(e))
            flash('{}'.format(str(e)), 'danger')
            return redirect(url_for('ui.index'))
        else:
            tz = datetime.datetime.now(tzlocal.get_localzone())
            runlog = os.path.join("ansible-ui-runlog-" + id + "-" + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S-') + (tz.tzname()) + ".log")
            session['runlog'] = runlog
            runlog_path = os.path.join(app.config['APP_PATH'], "logs", runlog)
            app.logger.info('%s executed playbook with id: %s', str(current_user).split(',')[0][3:], id)
            app.logger.info('created playbook runlog file %s', runlog)
            data = run_ssh_ui(cmd, runlog_path)
        return Response(stream_with_context(stream_template('run.html', data=data)), mimetype='text/html')

@ui_blueprint.route('/download', methods=['GET', 'POST'])
@login_required
def download():
    runlog = session.get('runlog', None)
    app.logger.info('%s downloaded runlog file %s', str(current_user).split(',')[0][3:], runlog)
    return send_from_directory(directory=os.path.join(app.config['APP_PATH'], "logs"), filename=runlog, as_attachment=True)

@ui_blueprint.route('/email', methods=['GET', 'POST'])
@login_required
def email():
    runlog = session.get('runlog', None)
    recipient_email = request.form['emails']
    try:
        send_email_ui(recipient_email, runlog)
    except Exception as e:
        app.logger.error('Mail to recipients %s failed because of %s', recipient_email, (str(e)))
        flash('Mail failed: {}'.format(str(e)), 'danger')
    else:
        app.logger.info('%s emailed runlog file %s to recipients : %s', str(current_user).split(',')[0][3:], runlog, recipient_email)
        flash('Email sent succesfully', 'info')
    finally:
        return redirect(url_for('ui.index'))

@ui_blueprint.route('/logout', methods=['POST', 'GET'])
@login_required
def logout():
    app.logger.info('user %s succesfully logged out!', str(current_user).split(',')[0][3:]) # Log who logged out
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('ui.login'))

@ui_blueprint.route('/runhistory', methods=['GET', 'POST'])
@login_required
def runhistory():
    page = request.args.get('page', 1, type=int)
    runhistory = Runhistory.query.order_by(Runhistory.time_started.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('ui.runhistory', page=runhistory.next_num) \
        if runhistory.has_next else None
    prev_url = url_for('ui.runhistory', page=runhistory.prev_num) \
        if runhistory.has_prev else None
    return render_template('runhistory.html', runhistory=runhistory.items, next_url=next_url, prev_url=prev_url)

@ui_blueprint.route('/viewlog/<logfile>', methods=['GET', 'POST'])
@login_required
def viewlog(logfile):
    file_path = os.path.join(app.config['APP_PATH'], "logs", logfile)
    text = open(file_path, 'r+')
    content = text.read()
    text.close()
    return render_template('viewlog.html', text=content)

# Error views
@app.errorhandler(404)
def error_404(error):
    return render_template('error_pages/404.html'), 404

@app.errorhandler(403)
def error_403(error):
    return render_template('error_pages/403.html'), 403

@app.errorhandler(500)
def error_500(error):
    app.logger.warning('user %s got 500 page', str(current_user).split(',')[0][3:])
    app.logger.warning('error is: %s', error)
    return render_template('error_pages/500.html'), 500
