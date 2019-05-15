"""SSH test and execute playlist functions for API"""
import os
from datetime import datetime
import logging
import tzlocal
import paramiko

from app.conf.config import APP_PATH, ANSIBLE_HOST, ANSIBLE_USER, ANSIBLE_KEY
from app.restapi.mailer_api import send_email_api
from app.database.createdb import db
from app.database.models import Runhistory
log = logging.getLogger('app')

def test_ssh(cmd):
    """ Master test_ssh function is called from both UI and API and Scheduled tasks. In turn it calls 3 nested functions to test various things."""
    sshtest = paramiko.SSHClient()
    sshtest.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    def test_connection():
        """ Test if we can connect to ANSIBLE_HOST """
        try:
            sshtest.connect(ANSIBLE_HOST, username=ANSIBLE_USER, key_filename=ANSIBLE_KEY)
        except Exception as e:
            raise ValueError("Connection Error: {}".format(str(e)))

    def test_files(testfiles):
        """ Test if ansible binary, inventory file and playbook exist on ANSIBLE_HOST """
        file_exist = {}
        for file in testfiles:
          # Other more straightforward way of testing this would be to use paramiko sftp stat file, but it doesn't take sudo meaning that your inventory and playbook files must be readable by ANSIBLE_USER
          #sftp = ssh.open_sftp()
          #print(sftp.stat(file))
          # Instead we will use shell command as this which will work regardless of whether you are using root on ANSIBLE_HOST or user with sudo privileges.
            stdin, stdout, stderr = sshtest.exec_command("sudo sh -c 'if [ ! -f % s ] ;  then echo 'False' ; else echo 'True' ; fi'" % file, get_pty=True)
            for line in stdout.readlines():
                file_exist['file'] = file
                file_exist['exists'] = line.rstrip()
            if file_exist['exists'] == 'False':
                raise ValueError('File does not exist IOError: "%s"' % (file_exist['file']))

    def test_if_running(cmd):
        """ Test if the same playbook process might be already running """
        cmd_run = {}
        # This works without sudo as ps command does not require sudo privilege, still to follow the same practice we wrap it in another quotes and execute it as sudo
        #stdin, stdout, stderr = ssh.exec_command("if [ $(ps -ef | grep '% s' | grep -v grep | wc -l) -ne 0 ]; then echo 'True'; else echo 'False';  fi" % cmd, get_pty=True)
        stdin, stdout, stderr = sshtest.exec_command("""sudo sh -c "if [ $(ps -ef | grep '% s' | grep -v grep | wc -l) -ne 0 ]; then echo 'True'; else echo 'False';  fi" """% cmd, get_pty=True)
        for line in stdout.readlines():
            cmd_run['command'] = cmd
            cmd_run['running'] = line.rstrip()
        if cmd_run['running'] == 'True':
            raise ValueError('Error: command already running on the server: %s try again later, or make sure that process is stopped!' % (cmd_run['command']))
    """ Master function calls 3 functions above """
    testfiles = cmd.split()[-4], cmd.split()[-2], cmd.split()[-1]
    process = cmd.replace('sudo', '')
    try:
        test_connection()
    except ValueError as e:
        raise
    else:
        try:
            test_files(testfiles)
        except ValueError as e:
            raise
        else:
            try:
                test_if_running(process)
            except ValueError as e:
                raise
    finally:
        sshtest.close()

def run_ssh_api(cmd, runlog_path, api_user, email):
    """ Function that executes ansible playbook for an API call """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ANSIBLE_HOST, username=ANSIBLE_USER, key_filename=ANSIBLE_KEY)
    tz = datetime.now(tzlocal.get_localzone())
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
    file = open(runlog_path, 'w')
    _user = api_user
    _type = 'API'
    _status = 'Running'
    _logfile = runlog_path.split('/')[-1]
    file.write('Begining execution of playbook file {} at {}\n'.format(cmd.split()[-1], datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z') + (tz.tzname())))
    try:
        record = Runhistory(user=_user, type=_type, status=_status, logfile=_logfile)
        db.session.add(record)
        db.session.commit()
    except Exception as e:
        log.error('ERROR: %s ', str(e))
        pass
    for line in iter(stdout.readline, ''):
        file.write(''.join(line))
    ssh.close()
    file.write('Completed execution of playbook file {} at {}\n'.format(cmd.split()[-1], datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z') + (tz.tzname())))
    file.close()
    try:
        item = Runhistory.query.filter_by(logfile=_logfile).all()
        for i in item:
            i.status = 'Completed'
        db.session.commit()
    except Exception as e:
        log.error('ERROR: %s ', str(e))
        pass
    # Check if we need to send a log via email
    if len(email) != 0:
        try:
            filename = os.path.relpath(runlog_path, os.path.join(APP_PATH, "logs"))
            recipient_email = " ".join(str(x) for x in email)
            send_email_api(recipient_email, filename, api_user)
        except Exception as e:
            log.error('Mail to recipients {} failed because of {}'.format(recipient_email, (str(e))))
        else:
            log.info('Mail sent succesfully to user {} with API runlog {}'.format(recipient_email, filename))
