#!/bin/sh
# Script to start docker services - first nginx
nginx -g 'daemon off;'

# and then gunicorn Uwsgi web server which start Flask application
/opt/flansible/bin/start-flansible.sh
