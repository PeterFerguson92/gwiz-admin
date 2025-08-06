web: gunicorn gwiz_admin.wsgi --log-file -
release: python manage.py migrate && python manage.py load_services