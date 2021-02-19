#!/usr/bin/env bash
service nginx start
gunicorn -b 127.0.0.1:4000 app:app --log-file /var/log/bioportal/gunicorn.log --log-level DEBUG
