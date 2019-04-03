"""This file contains all config parameters for Flansible app"""
#
# FLASK CONFIGS
#
DEBUG = "False"
SECRET_KEY = "secret"
#
#
# LOGGING CONFIG
APP_PATH = "/opt/flansible/app/"
LOG_FILE = "server.log"
#
#
# EMAIL CONFIG
MAILRELAY = "smtp.example.com"
MAIL_PORT = "25"
EMAIL_SENDER = "no-reply@example.com"
# APP_URL will show up in emails as a link and COMPANY_INFO will be included in email template
APP_URL = "https://flansible.example.com"
COMPANY_INFO = "Example Inc., 123 Main St., San Francisco CA 94104"
#
# LDAP CONFIGS
#
LDAP_HOST = "example.com"
LDAP_BASE_DN = "OU=ORG UNITS,DC=example,DC=com"
# Users DN to be prepended to the Base DN
LDAP_USER_DN = "OU=USERS"
# Groups DN to be prepended to the Base DN
LDAP_GROUP_DN = "OU=GROUPS"
# The Attribute you want users to authenticate to LDAP with.
LDAP_USER_LOGIN_ATTR = "sAMAccountName"
# The Username to bind to LDAP with
LDAP_BIND_USER_DN = "CN=Service Account,OU=Service Accounts,OU=SPECIAL,OU=ORG UNITS,DC=example,DC=com"
# The Password to bind to LDAP with
LDAP_BIND_USER_PASSWORD = "secret"
# The RDN attribute for your user schema on LDAP
LDAP_USER_RDN_ATTR = "CN"
# HERE you define LDAP AD group that can log in to your application!
LDAP_LOGIN_GROUP = "FlansibleAdmins"
LOGIN_GROUP_FULL_DN = str.join('', (LDAP_USER_RDN_ATTR, '=', LDAP_LOGIN_GROUP, ',', LDAP_GROUP_DN, ',', LDAP_BASE_DN))
#
#
#
#
# ANSIBLE CONFIGS
#
#
ANSIBLE_HOST = "ansibleserver.example.com"
ANSIBLE_USER = "flansible"
ANSIBLE_KEY = "/opt/flansible/app/id_rsa"
#
#
# DATABASE settings
SQLALCHEMY_TRACK_MODIFICATIONS = False
# API settings
#
#
JWT_SECRET_KEY = "secret"
MAX_APIUSERS = '3'
#
#
# RUN HISTORY PAGINATION - entries per page
POSTS_PER_PAGE = 20
#
# End of file
