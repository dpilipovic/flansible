#!/bin/bash
PIDS=$(ps ax | grep -i 'gunicorn' | grep -v grep | awk '{print $1}')

if [ -z "$PIDS" ]; then
  echo "No ansible-ui process to stop"
  exit 1
else
  kill -s TERM $PIDS
fi

