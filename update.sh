#!/bin/sh

source .env/bin/activate

python manage.py makemigrations

python manage.py migrate

python manage.py migrate django_cron
