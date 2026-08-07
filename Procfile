web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && python manage.py seed && gunicorn cognize.wsgi --bind 0.0.0.0:$PORT --workers 3
