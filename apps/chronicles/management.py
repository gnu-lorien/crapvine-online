from django.conf import settings
from django.db.models import signals
from django.utils.translation import ugettext_noop as _

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification
    
    def create_notice_types(app, created_models, verbosity, **kwargs):
        notification.create_notice_type("chronicles_new_member", _("New Chronicle Member"), _("a chronicle you are a member of has a new member"), default=1)
        notification.create_notice_type("chronicles_created_new_member", _("New Member Of Chronicle You Created"), _("a chronicle you created has a new member"), default=2)
        notification.create_notice_type("chronicles_new_chronicle", _("New Chronicle Created"), _("a new chronicle has been created"), default=1)
        notification.create_notice_type("chronicles_new_character", _("New Chronicle Character"), _("a chronicle you are a member of has a new character"))
        
    signals.post_syncdb.connect(create_notice_types, sender=notification)
else:
    print "Skipping creation of NoticeTypes as notification app not found"
