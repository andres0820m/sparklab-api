#!/bin/sh
python manage.py makemigrations
python manage.py migrate --noinput
python manage.py createsuperuser_db --username andres --password andres --noinput --email 'blank@email.com'
python manage.py runserver 0.0.0.0:8000