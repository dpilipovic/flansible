# flansible

I ❤ Ansible a lot. Like a lot. I also ❤ Flask. So once the need and an oportunity came up I've decided to create my own Flask powered Ansible UI, and threw in an API as well.
Main idea behind it was to popularize use of Ansible for automation tasks within my place of employment. With this in mind it became super easy for NOC people in the night shift to be able to restart and act upon various otherwise complex set of operations with a simple click of the button.
It also became easy to better utilize Ansible in CI/CD by making a simple API call when the new deployment code is ready to call upon a playbook. Lastly we could also automate things further by writing apps that would pick up an alert from monitoring and automatically restart an application without waking anybody up.

What this application offers is: 
UI with an easy to configure buttons to execute Ansible playbooks and watch their output.
UI uses LDAP for login of authorized users. These users can register their own API users.
Rest API which allows playbooks to be executed via API calls.


It is outside of the scope of this application: 
Validation/testing off playbooks. Assumption is that you will already test/validate and setup playbooks separately.
There are no separate privilege levels between users, meaning that all authorized users will have access to all configured buttons.


# INSTALLATION:

There are two ways to install the app. You can either grab a docker image from dockerhub (link to follow), or you can grab the code from this github repository.
If you are using docker image, you can skip to configuration section.

Our production setup is on Centos7, so instructions provided here are for this environment, but in general they apply for any linux distribution having in mind the difference in package install and commands.

## PYTHON3.6:

First, we need to install python3.6 as well as pip that corresponds to it.
Setup EPEL repository:
`yum install epel-release`
Install python3 packages from EPEL:
`yum install python36 python36-libs python36u-pip python36u-setuptools python36-devel python-rpm-macros python-srpm-macros python36-pip python36-setuptools`

CentOS image already comes with python2.7, actually yum package installer depends on it, so one way around it is to make python3 default, but change yum config files:
`unlink /usr/bin/python`
`ln -s /usr/bin/python3.6 /usr/bin/python`
Edit the following 2 files:
`/usr/bin/yum`
`/usr/libexec/urlgrabber-ext-down`
And in both change shebang line from #! /usr/bin/python to: #! /usr/bin/python2.7
Pip tool was also changed, in python3 it was moved into the python code, so correct way of calling it niw is: 
`python3.6 -m pip`
To make it less confusing regarding python2.7, you can add an alias to make python3.6 pip as default via command:
`python -m ensurepip --default-pip`

## CODE AND REQUIREMENTS:

Now grab the code from github repository. I suggest placing it under /opt/flansible directory, although feel free to place in your own structure. Within the directory, on a same level with run.py and requirements.txt, we want to create a python virtual environment:
`cd /opt/flansible`
`python -m venv venv`
Activate it:
`source venv/bin/activate`
and within it install all of the python modules we need:
`venv/bin/pip install -r requirements.txt`
Make sure that these are present with pip list command.
`deactivate`
And then run pip list again, to make sure that modules within venv are not globally shared. 

You can start the application now to test, via gunicorn UWSGI web server as such:
`/opt/flansible/venv/bin/python /opt/ansibleui/venv/bin/gunicorn -b 0.0.0.0:5000 -k gevent --worker-connections 1000 --timeout 900 run:app -D`

And go via browser to a port 5000 on your server and login page should load.
In case you decide to use different directory structure, one thing you will need to update is APP_PATH under conf/config.py file, as application will not start in case the directory specified there does not exist.

# CONFIGURATION:

There are 2 main files that need to be configured, and both are located under conf directory: config.py and buttons.yml.

## CONFIG.PY

Config.py is the main configuration file for the application. 
As a first thing you should change both SECRET_KEY and JWT_SECRET_KEY to some random values.
Generally accepted way of generating these is to go to python shell and run: 
`>>> import os`
`>>> os.urandom(24)`
 
 And then enter those values for keys. Do not enter os.urandom in the fields as that would cause these keys to be random everytime, and would break the application.
As for Email configs, use your own mail relay. Unless you want to send automatically to Amazon SMS, these in general don’t require a password, so libraries are configured as such.
Regarding Ansible configs – the application is configured to run on its own system and needs to be able to communicate to ansible server. For this you need to add a user on your ansible server, called flansible and give it bash access. Additionally, it needs to be added into the sudoers file as in:
`flansible      ALL=(ALL) NOPASSWD:ALL`
This will allow this user to sudo without getting prompted for password. Here we rely on public-private key combination rather than password. If you are using password authentication on your ansible server, you can add this at the bottom of your ansible servers /etc/ssh/sshd_config:
`Match User flansible
                 PasswordAuthentication no`
 Back on the flansible host, generate an ssh key:
  `ssh-keygen -t rsa `
and place the files under /opt/flansible/application/
Take the pub key and copy it. On ansible server, under newly added flansible user’s home directory, create subdirectory .ssh and place the contents of public key there under a file called authorized_keys.
Test that you can ssh from flansible host to ansible server as a flansible user.
I am not an expert in Active Directory by any means, and if you are like me, LDAP settings might seem as the biggest obstacle in configuration. It is true that you will need a help from your AD administrator to create a new AD group that will contain authorized users which can login. Also they will need to provide you with a Service Account with which you will query the domain, However, the rest of it is straight-forward. Basically, you just need to figure out the structure of your Active Directory leading to the group that AD administrators create.  That is the order of containers to which that group belongs. 
Helpful command in this regard is dsquery, which exists on any windows server joined to the domain in question.  Once you figure out the exact layout, you can take that and separate into BASE_DN and USER_DN/GROUP_DN.  You can also find more documentation on LDAP3_LOGIN library docs: https://flask-ldap3-login.readthedocs.io/en/latest/index.html 
To debug further from an application side, you can add print(data) in line 56 in application/__init__.py within save_user function.

## BUTTONS.YML

Once this is all setup, you need to look into configuring buttons.yml file.
This is where the Ansible Playbooks you want to add are setup.
Each button/operation has 4 required key-value pairs: button_name, button_description, _cmd and _id.
In addition there is an optional value of: api
button_name is the name that will be shown in the button on the home page
button_description is the description for this action that will show up next to the button on the home page
_id is the most important configuration parameter. It should be a unique alpabetical value without any spaces. It is passed to each operation, and according to _id value commands are triggered.
_id also has a secondary purpose that it is the API call endpoint - post calls will execute the playbooks via API call and GET calls will describe/list details about it from this same file.
_cmd is the ansible comand as you would run it on ansible server
api is optional if api: 'True' API call for this _id will be enabled, otherwise it is disabled.

## NGINX web server

# USING APPLICATION:

So how does it all function? LDAP users belonging to the authorized group can login to UI, where they get a home page on which buttons are loaded. Hitting any of these buttons executes a playbook and shows the output on a screen. Upon its completion users can download logfiles, or email the logfiles to multiple recipients. All runs are logged into the Run History page from where logs can bee seen as well. 
API page is the page for registering API users. Each LDAP user can register a MAX_APIUSERS from config.py. In addition to username user’s need to provide email address when registering API users. You can also select to receive emails with playbook runlogs whenever an API call finished executing a playbook. User’s can reset the API user’s password, as long as it belong to them, all other operations are done within Admin page.
Default Admin login is: admin changeme. One logged into Admin page you can reset the Admin password. Admin interface allows you to delete or edit Api users. 

