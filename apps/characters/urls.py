from django.conf.urls.defaults import *

from blog import views, models
from blog.forms import *


urlpatterns = patterns('',
    url(r'^upload_sheet/$', 'characters.views.upload_sheet', name='sheet_upload'),
    url(r'^list_sheets/$', 'characters.views.list_sheets', name='sheets_list'),
    url(r'^list_sheet/(?P<sheet_id>\d+)/$', 'characters.views.list_sheet', name='sheet_list'),
    url(r'^download_sheet/(?P<sheet_id>\d+)/$', 'characters.views.download_sheet', name='sheet_download')
)
