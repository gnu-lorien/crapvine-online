# coding=utf-8
from datetime import datetime, timedelta

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from tagging.fields import TagField
from tagging.models import Tag

from django.template.defaultfilters import slugify

import collections

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

EXPERIENCE_ENTRY_CHANGE_TYPES = [
    (0, "Earn"),
    (1, "Lose"),
    (2, "Set Earned To"),
    (3, "Spend"),
    (4, "Unspend"),
    (5, "Set Unspent To"),
    (6, "Comment"),
]

class ExperienceEntry(models.Model):
    reason = models.CharField(max_length=128)
    change = models.FloatField()
    change_type = models.PositiveSmallIntegerField(default=0, choices=EXPERIENCE_ENTRY_CHANGE_TYPES)
    earned = models.FloatField()
    unspent = models.FloatField()
    date = models.DateTimeField(default=datetime.now)

    class Meta:
        get_latest_by = "date"
        ordering = ["date"]
        verbose_name_plural = "experience entries"

    def __unicode__(self):
        return "<entry %s/>" % " ".join("%s=\"%s\"" % (fn, getattr(self, fn, '')) for fn in ExperienceEntry._meta.get_all_field_names() if fn not in ('id', 'sheet'))

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

    last_saved = models.DateTimeField(auto_now=True)

    experience_unspent = models.FloatField(default=0)
    experience_earned = models.FloatField(default=0)
    experience_entries = models.ManyToManyField(ExperienceEntry)

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

    def add_experience_entry(self, entry):
        try:
            last_experience_entry = self.experience_entries.reverse()[0]
        except IndexError:
            last_experience_entry = None
        self._calculate_earned_unspent_from_last(entry, last_experience_entry)
        if last_experience_entry is not None:
            if last_experience_entry.date >= entry.date:
                entry.date = last_experience_entry.date + timedelta(seconds=1)
        entry.save()
        #print "(", entry.unspent, ",", entry.earned, ") ->", entry.change_type
        self.experience_entries.add(entry)
        self.experience_unspent = entry.unspent
        self.experience_earned = entry.earned

    def _calculate_earned_unspent_from_last(self, entry, previous_entry):
        if previous_entry is None:
            FauxEntry = collections.namedtuple('FauxEntry', 'unspent earned')
            previous_entry = FauxEntry(0, 0)
            print "No last entry"
        entry.unspent = previous_entry.unspent
        entry.earned = previous_entry.earned
        print entry.change_type, "->", entry.get_change_type_display()
        print "previous_entry:", previous_entry
        if 3 == entry.change_type:
            entry.unspent = previous_entry.unspent - entry.change
        elif 0 == entry.change_type:
            entry.unspent = previous_entry.unspent + entry.change
            entry.earned = previous_entry.earned + entry.change
        elif 4 == entry.change_type:
            entry.unspent = previous_entry.unspent + entry.change
        elif 1 == entry.change_type:
            entry.earned = previous_entry.earned - entry.earned
        elif 2 == entry.change_type:
            entry.earned = entry.change
        elif 5 == entry.change_type:
            entry.unspent = entry.change
        elif 6:
            pass

    def update_experience_total(self):
        entries = self.experience_entries.all().order_by('-date')
        self.experience_unspent = entries[0].unspent
        self.experience_earned = entries[0].earned

    def save(self, *args, **kwargs):
        self.slug = slugify(self._get_slug())
        super(Sheet, self).save(*args, **kwargs)

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
    sect = models.CharField(max_length=128, default='')
    selfcontrol = models.PositiveSmallIntegerField()
    willpower = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=128)

    aura = models.SmallIntegerField(default=0)
    coterie = models.CharField(max_length=128, default='')
    id_text = models.CharField(max_length=128, default='')
    sire = models.CharField(max_length=128, default='')

    # These need to actually default to whatever value was just set for their permanents
    # Or... better yet... get turned into something that doesn't blow since we have this
    # great uploading framework now!!!
    tempcourage = models.PositiveSmallIntegerField(default=0)
    tempselfcontrol = models.PositiveSmallIntegerField(default=0)
    tempwillpower = models.PositiveSmallIntegerField(default=0)
    tempblood = models.PositiveSmallIntegerField(default=0)


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

