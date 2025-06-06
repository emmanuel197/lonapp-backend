#!/usr/bin/env bash
set -e

# 1) Run migrations
python manage.py migrate --noinput

# 2) Collect static files
python manage.py collectstatic --noinput

# 3) Launch Gunicorn
exec gunicorn lonapp.wsgi:application \
     --bind 0.0.0.0:8000 \
     --workers 3
