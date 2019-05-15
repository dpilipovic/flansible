""" All flask admin routes/views defined in here. """
import re
import logging

from flask import render_template, flash, request, Blueprint
from flask_login import current_user, login_required
# Needed to auto-generate password hash it and salt it
from werkzeug.security import generate_password_hash, check_password_hash

from app import app
from app.database.createdb import db
from app.conf.config import COMPANY_INFO
# Import Class/DB tables from Models
from app.database.models import Apiusers, Adminusers


log = logging.getLogger('app')

admin_blueprint = Blueprint('admin', __name__, template_folder='templates/admin')


""" Declare ROUTES """
@admin_blueprint.route('/', methods=['GET', 'POST'])
@login_required
def admin_index():
        if request.method == 'GET':
            if request.referrer == None:
               return render_template("index.html", buttons=buttons, show_admin_modal=True)
            elif (request.referrer).split('/')[3] == 'admin':
               return redirect(url_for('admin.apiusers'))
        if request.method == 'POST':
            admin_login = request.form['username']
            admin_pwd = request.form['password']
            valid_admin = db.session.query(Adminusers).filter_by(username=admin_login).first()
            try:
                if check_password_hash(valid_admin.password_hash, admin_pwd) == True:
                    app.logger.info('%s has logged in as %s into Admin page', str(current_user).split(',')[0][3:], admin_login)
                    apiusers = Apiusers.query.all()
                    return render_template("apiusers.html", apiusers=apiusers)
                else:
                    flash('Invalid admin credentials!', 'danger')
                    return render_template("index.html", buttons=buttons)
            except Exception as e:
                flash('Invalid admin credentials!', 'danger')
                app.logger.error('Invalid admin login attempt error: %s', e)
                return render_template("index.html", buttons=buttons)

@admin_blueprint.route('/apiusers', methods=['GET', 'POST'])
@login_required
def apiusers():
    if request.referrer == None:
        return render_template("index.html", buttons=buttons, show_admin_modal=True)
    elif (request.referrer).split('/')[3] == 'admin':
        apiusers = Apiusers.query.all()
        return render_template("apiusers.html", apiusers=apiusers)
    else:
        return render_template("index.html", buttons=buttons, show_admin_modal=True)

@admin_blueprint.route('/delete_user', methods=['POST'])
@login_required
def delete_user():
    if request.referrer == None:
        return render_template("index.html", buttons=buttons, show_admin_modal=True)
    # This is only to allow post coming from one of the admin URL's otherwise redirect to admin login modal.
    elif (request.referrer).split('/')[3] == 'admin':
        uid = request.form['pass_value']
        to_delete = str(Apiusers.query.get(uid))
        try:
            Apiusers.query.filter(Apiusers.id == uid).delete()
            db.session.commit()
            app.logger.info('%s has deleted an API user %s in Admin page', str(current_user).split(',')[0][3:], to_delete)
            flash('Record succesfully deleted!', 'info')
            return redirect(url_for('admin.apiusers'))
        except Exception as e:
            db.session.rollback()
            app.logger.error('ERROR: %s ', str(e))
            flash('{}'.format(str(e)), 'danger')
            return redirect(url_for('admin.apiusers'))
    else:
        return render_template("index.html", buttons=buttons, show_admin_modal=True)

@admin_blueprint.route('/edit_user', methods=['POST'])
@login_required
def edit_user():
    if request.referrer == None:
        return render_template("index.html", buttons=buttons, show_admin_modal=True)
    elif (request.referrer).split('/')[3] == 'admin':
        apiusers = Apiusers.query.all()
        _id = request.form['pass_id_value']
        _username = request.form['pass_username']
        _email = request.form['pass_email']
        _notify = request.form['pass_notify']
        _notify = int(_notify == 'True')
        item = Apiusers.query.get(_id)
        try:
            item.username = _username
            item.email = _email
            item.notify = _notify
            db.session.commit()
            flash('Record succesfully edited!', 'info')
            return redirect(url_for('admin.apiusers'))
        except Exception as e:
            db.session.rollback()
            app.logger.error('ERROR: %s ', str(e))
            flash('{}'.format(str(e)), 'danger')
            return redirect(url_for('admin.apiusers'))
    else:
        return render_template("index.html", buttons=buttons, show_admin_modal=True)

@admin_blueprint.route('/multidelete', methods=['POST'])
@login_required
def multidelete():
    if request.referrer == None:
        return render_template("index.html", buttons=buttons, show_admin_modal=True)
    elif (request.referrer).split('/')[3] == 'admin':
        apiusers = Apiusers.query.all()
        multi_delete = request.form['pass_checkedvalue'].split(",")
        multideletenames = str(Apiusers.query.filter(Apiusers.id.in_(multi_delete)).all()).strip("[]")
        try:
            Apiusers.query.filter(Apiusers.id.in_(multi_delete)).delete(synchronize_session=False)
            db.session.commit()
            app.logger.info('%s has deleted an API users: %s in Admin page', str(current_user).split(',')[0][3:], multideletenames)
            flash('Records succesfully deleted!', 'info')
            return redirect(url_for('admin.apiusers'))
        except Exception as e:
            db.session.rollback()
            app.logger.error('ERROR: %s ', str(e))
            flash('{}'.format(str(e)), 'danger')
            return redirect(url_for('admin.apiusers'))
    else:
        return render_template("index.html", buttons=buttons, show_admin_modal=True)

@admin_blueprint.route('/admin_reset', methods=['POST'])
@login_required
def admin_reset():
    if request.referrer == None:
        return render_template("index.html", buttons=buttons, show_admin_modal=True)
    elif (request.referrer).split('/')[3] == 'admin':
        admin_login = 'admin'
        current_pwd = request.form['current_pwd']
        new_pwd = request.form['pass1']
        confirm_pwd = request.form['pass2']
        # Validation section:
        if not new_pwd:
            flash('Password not provided.', 'danger')
            app.logger.error('Reset admin credentials attempt failed - password not provided by user %s', str(current_user).split(',')[0][3:])
            return redirect(url_for('admin.apiusers'))
        if not re.match('\d.*[A-Z]|[A-Z].*\d', new_pwd):
            flash('Password must contain 1 capital letter and 1 number.', 'danger')
            app.logger.error('Reset admin credentials attempt failed by user %s - password must contain 1 capital letter and 1 number', str(current_user).split(',')[0][3:])
            return redirect(url_for('admin.apiusers'))
        if len(new_pwd) < 8 or len(new_pwd) > 50:
            flash('Password must be between 8 and 50 characters.', 'danger')
            app.logger.error('Reset admin credentials attempt failed by user %s - password must be between 8 and 50 characters.', str(current_user).split(',')[0][3:])
            return redirect(url_for('admin.apiusers'))
        # Reset Admin password if everything is ok.
        _password_hash = generate_password_hash(new_pwd)
        valid_admin = db.session.query(Adminusers).filter_by(username=admin_login).first()
        if check_password_hash(valid_admin.password_hash, current_pwd) == True:
            try:
                item = Adminusers.query.filter_by(username='admin').one()
                item.password_hash = _password_hash
                db.session.commit()
                app.logger.info('%s has reset an admin credentials!', str(current_user).split(',')[0][3:])
                flash('Admin credentials have been reset!', 'info')
                return redirect(url_for('admin.apiusers'))
            except Exception as e:
                db.session.rollback()
                app.logger.error('ERROR: %s ', str(e))
                flash('{}'.format(str(e)), 'danger')
                return redirect(url_for('admin.apiusers'))
        else:
            flash('Invalid admin credentials!', 'danger')
            return redirect(url_for('admin.apiusers'))
    else:
        return render_template("index.html", buttons=buttons, show_admin_modal=True)
