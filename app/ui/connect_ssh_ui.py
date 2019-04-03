"""SSH test and execute playlist functions for UI and API"""
import logging
from datetime import datetime
import tzlocal
import paramiko
import gevent

from flask_login import current_user

from app.conf.config import ANSIBLE_HOST, ANSIBLE_USER, ANSIBLE_KEY
from app.database.createdb import db
from app.database.models import Runhistory

log = logging.getLogger('app')


ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())


def test_connection():
    """ Test if we can connect to ANSIBLE_HOST """
    try:
        ssh.connect(ANSIBLE_HOST, username=ANSIBLE_USER, key_filename=ANSIBLE_KEY)
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
        stdin, stdout, stderr = ssh.exec_command("sudo sh -c 'if [ ! -f % s ] ;  then echo 'False' ; else echo 'True' ; fi'" % file, get_pty=True)
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
    stdin, stdout, stderr = ssh.exec_command("""sudo sh -c "if [ $(ps -ef | grep '% s' | grep -v grep | wc -l) -ne 0 ]; then echo 'True'; else echo 'False';  fi" """% cmd, get_pty=True)
    for line in stdout.readlines():
        cmd_run['command'] = cmd
        cmd_run['running'] = line.rstrip()
    if cmd_run['running'] == 'True':
        raise ValueError('Error: command already running on the server: %s try again later, or make sure that process is stopped!' % (cmd_run['command']))

def test_ssh(cmd):
    """ Master test_ssh function is called from both UI and API. In turn it calls previous 3 functions """
    testfiles = cmd.split()[-4], cmd.split()[-2], cmd.split()[-1]
    process = cmd.replace('sudo', '')
    try:
        test_connection()
    except ValueError as e:
        raise
        ssh.close()
    else:
        try:
            test_files(testfiles)
        except ValueError as e:
            raise
            ssh.close()
        else:
            try:
                test_if_running(process)
            except ValueError as e:
                raise
                ssh.close()

def run_ssh_ui(cmd, runlog_path):
    """ Function that executes ansible playbook from UI when a button is clicked """
    tz = datetime.now(tzlocal.get_localzone())
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
    file = open(runlog_path, 'w')
    _user = str(current_user).split(',')[0][3:]
    _type = 'UI'
    _status = 'running'
    _logfile = runlog_path.split('/')[-1]
    try:
        record = Runhistory(user=_user, type=_type, status=_status, logfile=_logfile)
        db.session.add(record)
        db.session.commit()
    except Exception as e:
        log.error('ERROR: %s ', str(e))
        pass
    file.write('Begining execution of playbook file {} at {}\n'.format(cmd.split()[-1], datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z') + (tz.tzname())))
    for line in iter(stdout.readline, ''):
        gevent.sleep(0.3)                           # Don't need this just shows the text streaming, using gevent for it not to block other users
        yield line.rstrip()
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
    log.info('Completed execution of playbook with command: %s', cmd)
