from django.conf.urls.defaults import *

from blog import views, models
from blog.forms import *


urlpatterns = patterns('characters.views',
    url(r'^upload_sheet/$', 'upload_sheet', name='sheet_upload'),
    url(r'^list_sheets/$', 'list_sheets', name='sheets_list'),
    url(r'^list_sheet/(?P<sheet_slug>[-\w]+)/$', 'list_sheet', name='sheet_list'),
    url(r'^history_sheet/(?P<sheet_slug>[-\w]+)/$', 'history_sheet', name='sheet_history'),
    url(r'^download_sheet/(?P<sheet_slug>[-\w]+)/$', 'download_sheet', name='sheet_download'),
    url(r'^edit_vampire_sheet_attributes/(?P<sheet_slug>[-\w]+)/$', 'edit_vampire_sheet_attributes', name='sheet_vampire_edit_attributes'),

    # Traits
    url(r'^edit_sheet_traitlist/(?P<sheet_slug>[-\w]+)/(?P<traitlistname_slug>[-\w]+)/$', 'edit_traitlist', name='sheet_edit_traitlist'),
    url(r'^reorder_sheet_traitlist/(?P<sheet_slug>[-\w]+)/(?P<traitlistname_slug>[-\w]+)/$', 'reorder_traitlist', name='sheet_reorder_traitlist'),
    url(r'^edit_sheet_trait/(?P<sheet_slug>[-\w]+)/(?P<trait_id>\d+)/$', 'edit_trait', name='sheet_edit_trait'),
    url(r'^delete_sheet_trait/(?P<sheet_slug>[-\w]+)/(?P<trait_id>\d+)/$', 'delete_trait', name='sheet_delete_trait'),
    url(r'^new_sheet_trait/(?P<sheet_slug>[-\w]+)/(?P<traitlistname_slug>[-\w]+)/$', 'new_trait', name='sheet_new_trait'),
)
