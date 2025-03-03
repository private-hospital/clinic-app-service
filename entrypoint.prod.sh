#!/usr/bin/bash
echo "Starting Django application..."
python3 manage.py migrate --noinput
python3 -m gunicorn --bind 0.0.0.0:8000 --workers 3 private_hospital.wsgi:application