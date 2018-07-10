python manage.py makemigrations
python manage.py migrate
python manage.py migrate django_cron

mkdir storage

# run cron jobs ( Forced )

python manage.py runcrons --force