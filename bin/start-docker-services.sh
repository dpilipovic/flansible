#!/bin/sh
# Script to start docker services - both nginx and application.
nginx -g 'daemon off;'
/opt/flansible/bin/start-flansible.sh
