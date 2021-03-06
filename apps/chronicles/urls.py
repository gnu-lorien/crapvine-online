from django.conf.urls.defaults import *

from chronicles.models import Chronicle

from groups.bridge import ContentBridge


bridge = ContentBridge(Chronicle, 'chronicles')

urlpatterns = patterns('chronicles.views',
    url(r'^$', 'chronicles', name="chronicle_list"),
    url(r'^create/$', 'create', name="chronicle_create"),
    url(r'^your_chronicles/$', 'your_chronicles', name="your_chronicles"),
    
    # chronicle-specific
    url(r'^chronicle/(?P<group_slug>[-\w]+)/$', 'chronicle', name="chronicle_detail"),
    url(r'^chronicle/(?P<group_slug>[-\w]+)/delete/$', 'delete', name="chronicle_delete"),
    url(r'^chronicle/(?P<group_slug>[-\w]+)/edit_membership/(?P<username>[\w\._-]+)/$', 'edit_membership', name='chronicle_edit_membership'),
    url(r'^chronicle/(?P<group_slug>[-\w]+)/members/$', 'list_members', name='chronicle_members'),
)

urlpatterns += bridge.include_urls('characters.urls', r'^chronicle/(?P<chronicle_slug>[-\w]+)/characters/')
