from django.core.urlresolvers import reverse
from django.contrib.auth.models import  User
from django.utils.translation import ugettext_lazy as _
from django.db import models

from groups.base import Group
from characters.models import Sheet

class Chronicle(Group):
    
    member_users = models.ManyToManyField(User, through='ChronicleMember', verbose_name=_('members'))

    private = models.BooleanField(_('private'), default=False)
    
    def get_absolute_url(self):
        return reverse('chronicle_detail', kwargs={'group_slug': self.slug})

    def member_queryset(self):
        return self.member_users.all()

    def user_is_member(self, user):
        return ChronicleMember.objects.filter(chronicle=self, user=user).count() > 0

    def get_url_kwargs(self):
        return {'chronicle_slug': self.slug}

    def get_sheets_for_user(self, user):
        if not self.user_is_member(user):
            return []

        cm = ChronicleMember.objects.get(user=user, chronicle=self)
        if 0 == cm.membership_role:
            return self.content_objects(Sheet)
        return self.content_objects(Sheet).filter(player=user)

class ChronicleMember(models.Model):
    chronicle = models.ForeignKey(Chronicle, related_name="members", verbose_name=_('chronicle'))
    user = models.ForeignKey(User, related_name='chronicles', verbose_name=_('user'))

    CHOICES = zip(range(5), ('storyteller', 'narrator', 'player', 'travelling_player', 'other'))
    membership_role = models.PositiveSmallIntegerField(choices=CHOICES, default=2)
    membership_role_other = models.CharField(default='', max_length=128)
