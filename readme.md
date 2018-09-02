cd psq_api

virtualenv -p python3 .env

source .env/bin/activate

# Install reqs

pip install -r requirements.txt 

pip freeze > requirements.txt

pip install gunicorn

python manage.py makemigrations

python manage.py migrate

python manage.py migrate django_cron


https://docs.djangoproject.com/en/2.0/topics/migrations/

# create super user

python manage.py createsuperuser

# cron jobs

http://django-cron.readthedocs.io/en/latest/installation.html

python manage.py runcrons --force

# locale

django-admin makemessages -l es
django-admin compilemessages

# kill debug process

sudo lsof -t -i tcp:8001 | xargs kill -9

# dns

https://www.hiroom2.com/2018/05/06/ubuntu-1804-bind-en/
https://www.digitalocean.com/community/tutorials/how-to-configure-bind-as-a-private-network-dns-server-on-ubuntu-16-04
https://www.digitalocean.com/community/tutorials/how-to-configure-bind-as-a-caching-or-forwarding-dns-server-on-ubuntu-14-04

# services

service --status-all