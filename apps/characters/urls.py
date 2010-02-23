from django.conf.urls.defaults import *

from blog import views, models
from blog.forms import *


urlpatterns = patterns('',
    # upload sheets
    url(r'^upload_sheet/$', 'characters.views.upload_sheet', name='sheet_upload')
)
