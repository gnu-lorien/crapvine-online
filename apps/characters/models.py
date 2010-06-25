# coding=utf-8
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
            vstr = ''
            if show_val:
                vstr = (" x%s" % (self.value))
            if tally_val:
                vstr += " %s" % (self.tally_str())
            nstr = (" (%s)" % (self.note)) if show_note else ''
            return "%s%s%s" % (self.name, vstr, nstr)
        elif self.display_preference == 3:
            vstr = " %s" % (self.tally_str()) if tally_val else ''
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
            itrange = self.value if self.value >= 1 else 1
            for i in range(itrange):
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

class Expendable(models.Model):
    name = models.CharField(max_length=128)
    value = models.IntegerField(default=1)
    modifier = models.IntegerField(default=0)
    dot_character = models.CharField(max_length=8, default='O')
    modifier_character = models.CharField(max_length=8, default='Õ')

class TraitListName(models.Model):
    name = models.CharField(max_length=128, unique=True)

    def __unicode__(self):
        return self.name

class Sheet(models.Model):
    name = models.CharField(max_length=128)
    traits = models.ManyToManyField(Trait, through='TraitList')
    player = models.ForeignKey(User, related_name='personal_characters')
    #narrator = models.ForeignKey(User, related_name='narrated_characters')
    # TODO Change this to support narrators in and outside of the database?
    narrator = models.CharField(max_length=128)
    slug = models.SlugField()
    home_chronicle = models.CharField(max_length=128) # Make this refer to a real thing from another app

    start_date = models.DateTimeField(default=datetime.now)
    last_modified = models.DateTimeField(default=datetime.now)

    npc = models.BooleanField(default=False)

    notes = models.TextField(default='', blank=True)
    biography = models.TextField(default='', blank=True)

    status = models.CharField(max_length=128)

    def __unicode__(self):
        return self.name

    def _get_slug(self):
        return " ".join([self.player.username, self.name])

    def get_traitlist(self, name):
        return self.traits.filter(traitlist__name__name=name).order_by('traitlist__display_order')

    def add_trait(self, traitlist_name, trait):
        trait.save()
        try:
            traitlist_name_obj = TraitListName.objects.get(name=traitlist_name)
        except TraitListName.DoesNotExist:
            traitlist_name_obj = TraitListName.objects.create(name=traitlist_name)
        traitlist = TraitList.objects.filter(sheet=self, name=traitlist_name_obj).order_by('display_order')
        TraitList.objects.create(sheet=self, trait=trait, display_order=len(traitlist), name=traitlist_name_obj).save()

    def insert_trait(self, traitlist_name, trait, display_order):
        trait.save()
        traitlist_name_obj = TraitListName.objects.get(name=traitlist_name)
        traitlist = TraitList.objects.filter(sheet=self, name=traitlist_name_obj, display_order__gte=display_order).order_by('display_order')
        for traitlist_obj in traitlist:
            traitlist_obj.display_order += 1
            traitlist_obj.save()
        TraitList.objects.create(sheet=self, trait=trait, display_order=display_order, name=traitlist_name_obj).save()

class VampireSheet(Sheet):
    nature = models.CharField(max_length=128)
    demeanor = models.CharField(max_length=128)
    blood = models.PositiveSmallIntegerField()
    clan = models.CharField(max_length=128)
    conscience = models.PositiveSmallIntegerField()
    courage = models.PositiveSmallIntegerField()
    generation = models.PositiveSmallIntegerField()
    path = models.CharField(max_length=128)
    pathtraits = models.PositiveSmallIntegerField()
    physicalmax = models.PositiveSmallIntegerField()
    sect = models.CharField(max_length=128)
    selfcontrol = models.PositiveSmallIntegerField()
    willpower = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=128)

    aura = models.SmallIntegerField()
    coterie = models.CharField(max_length=128)
    id_text = models.CharField(max_length=128)
    sire = models.CharField(max_length=128)

    tempcourage = models.PositiveSmallIntegerField()
    tempselfcontrol = models.PositiveSmallIntegerField()
    tempwillpower = models.PositiveSmallIntegerField()
    tempblood = models.PositiveSmallIntegerField()


class TraitList(models.Model):
    sheet = models.ForeignKey(Sheet)
    trait = models.ForeignKey(Trait)
    name = models.ForeignKey(TraitListName)
    display_order = models.IntegerField()
    sorted = models.BooleanField(default=True)
    atomic = models.BooleanField(default=False)
    negative = models.BooleanField(default=False)

    def __unicode__(self):
        return "->".join([self.sheet.name, self.name.name, self.trait.name])

