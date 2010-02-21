from django.conf import settings
from django.db.models import signals
from django.utils.translation import ugettext_noop as _

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification

    def create_notice_types(app, created_models, verbosity, **kwargs):
        notification.create_notice_type("characters_friend_sheet", _("Friend Added a Character Sheet"), _("a friend of yours added a character sheet"), default=2)
        notification.create_notice_type("characters_sheet_comment", _("New Comment on Character Sheet"), _("a comment was made on one of your character sheets"), default=2)

    signals.post_syncdb.connect(create_notice_types, sender=notification)
else:
    print "Skipping creation of NoticeTypes as notification app not found"
