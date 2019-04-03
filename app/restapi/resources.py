"""Resources used by API are defined in this module"""
import datetime
import os
import threading
import logging
import tzlocal

from flask_jwt import jwt_required, current_identity
from flask import jsonify, session, abort
from sqlalchemy import text
from flask_restful import Resource

from app import buttons
from app.database.createdb import db
from app.restapi.connect_ssh_api import test_ssh, run_ssh_api
from app.conf.config import APP_PATH
log = logging.getLogger('app')

class AllIDs(Resource):
    """ API GET resource that lists all available API calls mapped to /list """
    @jwt_required()
    def get(self):
        # return all the API calls  :)
        api = [item for item in buttons if item.get("api") == "True"]
        return {'commands': api}

class RetrieveIDs(Resource):
    """ API GET request will list all details about command from buttons.yml, mapped to _id """
    @jwt_required()
    def get(self, id):
        api = [item for item in buttons if item.get("api") == "True"]
        b = [b for b in api if b['_id'] == id]
        if len(b) == 0:
            abort(404)
        return jsonify({'api_call_details': b[0]})

class ExecIDs(Resource):
    """ API POST request to ID which executes playbook as a thread in the background, mapped to _id """
    @jwt_required()
    def post(self, id):
        cmd = None
        api = [item for item in buttons if item.get("api") == "True"]
        for btn in api:
            if btn['_id'] == id:
                cmd = (btn['_cmd'])
        if cmd == None:
            abort(404)
        try:
            test_ssh(cmd)
        except ValueError as e:
            return jsonify({"status": "error", 'message' : str(e)})
        else:
            tz = datetime.datetime.now(tzlocal.get_localzone())
            runlog = os.path.join("api-runlog-" + id + "-" + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S-') + (tz.tzname()) + ".log")
            session['runlog'] = runlog
            runlog_path = os.path.join(APP_PATH, "logs", runlog)
            api_user = str(current_identity)
            # Obtain email if API user has selected to be notified, log if problem with database and continue without sending mail
            try:
                sql = text('select email from apiusers where username =:ci and notify="1"')
                result = db.engine.execute(sql, {'ci': str(current_identity)})
                email = [row[0] for row in result]
            except Exception as e:
                log.info('Error querying the database %s', str(e))
                email = ''
            log.info('API user: %s executed playbook with id: %s via API call', current_identity, id)
            log.info('created playbook runlog file %s for this API call', runlog)
            # We are running the API call execution of playlist as a thread - due to this we send "OK command submitted for execution" json response back and spin off a separate thread which then takes care of it.
            api_thread = threading.Thread(target=run_ssh_api, args=(cmd, runlog_path, api_user, email))
            api_thread.start()
            return jsonify({"status" : "success", "message" : "command " + str(cmd) + " succesfully submited for execution"})
