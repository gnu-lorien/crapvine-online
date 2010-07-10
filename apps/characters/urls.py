from django.conf.urls.defaults import *

from blog import views, models
from blog.forms import *


urlpatterns = patterns('characters.views',
    url(r'^upload_sheet/$', 'upload_sheet', name='sheet_upload'),
    url(r'^list_sheets/$', 'list_sheets', name='sheets_list'),
    url(r'^list_sheet/(?P<sheet_id>\d+)/$', 'list_sheet', name='sheet_list'),
    url(r'^download_sheet/(?P<sheet_id>\d+)/$', 'download_sheet', name='sheet_download'),
    url(r'^edit_vampire_sheet_attributes/(?P<sheet_id>\d+)/$', 'edit_vampire_sheet_attributes', name='sheet_vampire_edit_attributes'),
    url(r'^edit_vampire_sheet_traitlist/(?P<sheet_id>\d+)/$', 'edit_vampire_sheet_traitlist', name='sheet_vampire_edit_traitlist'),
)
