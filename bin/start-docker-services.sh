#!/bin/sh
# Script to start docker services - first gunicorn uwsgi server which starts Flask app
/opt/flansible/bin/start-flansible.sh &

# and then nginx proxy in front of it
nginx -g 'daemon off;' 


