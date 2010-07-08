from django.core.urlresolvers import reverse
from django.contrib.auth.models import  User
from django.utils.translation import ugettext_lazy as _
from django.db import models

from groups.base import Group
from characters.models import Sheet

class Chronicle(Group):
    
    members = models.ManyToManyField(User, related_name='chronicles', verbose_name=_('members'))
    
    def get_absolute_url(self):
        return reverse('chronicle_detail', kwargs={'group_slug': self.slug})
    
    def get_url_kwargs(self):
        return {'group_slug': self.slug}
