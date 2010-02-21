from datetime import datetime

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from tagging.fields import TagField
from tagging.models import Tag

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification
else:
    notification = None

#lass Sheet(models.Model):
#   """Sheet model."""
#   STATUS_CHOICES = (
#       (1, _('Draft')),
#       (2, _('Public')),
#   )
#   title           = models.CharField(_('title'), max_length=200)
#   slug            = models.SlugField(_('slug'))
#   author          = models.ForeignKey(User, related_name="added_posts")
#   creator_ip      = models.IPAddressField(_("IP Address of the Post Creator"), blank=True, null=True)
#   body            = models.TextField(_('body'))
#   tease           = models.TextField(_('tease'), blank=True)
#   status          = models.IntegerField(_('status'), choices=STATUS_CHOICES, default=2)
#   allow_comments  = models.BooleanField(_('allow comments'), default=True)
#   publish         = models.DateTimeField(_('publish'), default=datetime.now)
#   created_at      = models.DateTimeField(_('created at'), default=datetime.now)
#   updated_at      = models.DateTimeField(_('updated at'))
#   markup          = models.CharField(_(u"Post Content Markup"), max_length=20,
#                             choices=settings.MARKUP_CHOICES,
#                             null=True, blank=True)
#   tags            = TagField()
#   
#   class Meta:
#       verbose_name        = _('sheet')
#       verbose_name_plural = _('sheets')
#       ordering            = ('-publish',)
#       get_latest_by       = 'publish'
#
#   def __unicode__(self):
#       return self.title
#
#   def get_absolute_url(self):
#       return ('characters_sheet', None, {
#           'username': self.author.username,
#           'year': self.publish.year,
#           'month': "%02d" % self.publish.month,
#           'slug': self.slug
#   })
#   get_absolute_url = models.permalink(get_absolute_url)
#
#   def save(self, force_insert=False, force_update=False):
#       self.updated_at = datetime.now()
#       super(models.Model, self).save(force_insert, force_update)

# handle notification of new comments
from threadedcomments.models import ThreadedComment
def new_comment(sender, instance, **kwargs):
    if isinstance(instance.content_object, Sheet):
        sheet = instance.content_object
        if notification:
            notification.send([sheet.author], "characters_sheet_comment",
                {"user": instance.user, "sheet": sheet, "comment": instance})
models.signals.post_save.connect(new_comment, sender=ThreadedComment)

DISPLAY_PREFERENCES = [
    (0, "name"),
    (1, "name xvalue (note)"),
    (2, "name xvalue dot (note)"),
    (3, "name dot (note)"),
    (4, "name (value, note)"),
    (5, "name (note)"),
    (6, "name (value)"),
    (7, "name (note)dotname (note)dot by value"),
    (8, "dot"),
    (9, "value"),
    (10,"note")
]

class Trait(models.Model):
    name = models.CharField(max_length=128)
    note = models.CharField(max_length=128, default='', blank=True)
    value = models.IntegerField(default=1)

    display_preference = models.SmallIntegerField(default=1, choices=DISPLAY_PREFERENCES)
    dot_character = models.CharField(max_length=8, default='O')

    def __show_note(self):
        return self.note != Trait._meta.get_field_by_name('note')[0].get_default()
    def __show_val(self):
        return self.value >= 1
    def __tally_val(self):
        return self.__show_val()
    def tally_str(self):
        if self.value >= 1:
            return self.dot_character * self.value
        else:
            return ''

    def __unicode__(self):
        show_note = self.__show_note()
        show_val  = self.__show_val()
        tally_val = self.__tally_val()

        if self.display_preference == 0:
            return self.name
        elif self.display_preference == 1:
            vstr = (" x%s" % (self.value)) if show_val else ''
            nstr = (" (%s)" % (self.note)) if show_note else ''
            return "%s%s%s" % (self.name, vstr, nstr)
        elif self.display_preference == 2:
            if show_val:
                vstr = (" x%s" % (self.value))
            if tally_val:
                vstr += " %s" % (self.tally_str())
            nstr = (" (%s)" % (self.note)) if show_note else ''
            return "%s%s%s" % (self.name, vstr, nstr)
        elif self.display_preference == 3:
            if tally_val:
                vstr = " %s" % (self.tally_str())
            nstr = (" (%s)" % (self.note)) if show_note else ''
            return "%s%s%s" % (self.name, vstr, nstr)
        elif self.display_preference == 4:
            paren_str = ""
            if show_note and show_val:
                paren_str = " (%s, %s)" % (self.value, self.note)
            elif show_note and not show_val:
                paren_str = " (%s)" % (self.note)
            elif show_val and not show_note:
                paren_str = " (%s)" % (self.value)
            return "%s%s" % (self.name, paren_str)
        elif self.display_preference == 5:
            paren_str = ""
            if show_note:
                paren_str = " (%s)" % (self.note)
            return "%s%s" % (self.name, paren_str)
        elif self.display_preference == 6:
            paren_str = ""
            if show_val:
                paren_str = " (%s)" % (self.value)
            return "%s%s" % (self.name, paren_str)
        elif self.display_preference == 7:
            paren_str = (" (%s)" % (self.note)) if show_note else ''
            dstr = "%s%s" % (self.name, paren_str)
            its = []
            for i in range(self.value):
                its.append(dstr)
            return self.dot_character.join(its)
        elif self.display_preference == 8:
            return self.tally_str()
        elif self.display_preference == 9:
            if show_val:
                return "%d" % (self.value)
            else:
                return ''
        elif self.display_preference == 10:
            if show_note:
                return self.note
            else:
                return ''

        return 'NOCING'

class Expendable(Trait):
    modifier = models.IntegerField(default=0)

class Sheet(models.Model):
    name = models.CharField(max_length=128)
    traits = models.ManyToManyField(Trait, through='TraitList')

    def __unicode__(self):
        return self.name

class TraitList(models.Model):
    sheet = models.ForeignKey(Sheet)
    trait = models.ForeignKey(Trait)
    name = models.SmallIntegerField(choices=((1, 'Physical'), (2, 'Social')))
    display_order = models.IntegerField()
    sorted = models.BooleanField(default=True)
    atomic = models.BooleanField(default=False)
    negative = models.BooleanField(default=False)

    def __unicode__(self):
        return "->".join([self.sheet.name, self.get_name_display(), self.trait.name])

