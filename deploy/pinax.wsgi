import os
import sys

# redirect sys.stdout to sys.stderr for bad libraries like geopy that uses
# print statements for optional import exceptions.
sys.stdout = sys.stderr

from os.path import abspath, dirname, join

sys.path.insert(0, '/home/ourianet/public_html/virtfs/lib/python2.6/site-packages')
sys.path.insert(0, '/home/ourianet/public_html')

sys.path.insert(0, '/home/ourianet/public_html/virtfs/lib/python2.6/site-packages')
sys.path.insert(0, '/home/ourianet/public_html/virtfs/lib/python2.6')

sys.path.insert(0, '/home/ourianet/public_html/test-crapvine-online')
sys.path.insert(0, '/home/ourianet/public_html/test-crapvine-online/apps')

from django.conf import settings
os.environ["DJANGO_SETTINGS_MODULE"] = "test-crapvine-online.settings"


from django.core.handlers.wsgi import WSGIHandler
application = WSGIHandler()

