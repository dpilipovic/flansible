#!/bin/bash
cd /opt/flansible ;
/opt/flansible/venv/bin/python /opt/flansible/venv/bin/gunicorn -b localhost:8000 -k gevent --worker-connections 1000 --timeout 900 run:app -D;
/opt/flansible/venv/bin/python /opt/flansible/venv/bin/gunicorn -b localhost:8001 -k gevent --worker-connections 1000 --timeout 900 run:app -D;
/opt/flansible/venv/bin/python /opt/flansible/venv/bin/gunicorn -b localhost:8002 -k gevent --worker-connections 1000 --timeout 900 run:app -D;
/opt/flansible/venv/bin/python /opt/flansible/venv/bin/gunicorn -b localhost:8003 -k gevent --worker-connections 1000 --timeout 900 run:app -D;
