rm dev.db
python manage.py syncdb --noinput
python manage.py migrate characters
python manage.py migrate chronicles

python manage.py debugsqlshell < upload_chronicle_camarilla_five_bin.timeit > out
