# coding=utf-8
from datetime import datetime, timedelta
import logging
# Only need this when debugging
#import sys
#logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
from pprint import pformat
from django.core.urlresolvers import reverse

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from tagging.fields import TagField
from tagging.models import Tag

from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType

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
    reason = models.TextField()
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

class Expendable(models.Model):
    name = models.CharField(max_length=128)
    value = models.IntegerField(default=1)
    modifier = models.IntegerField(default=0)
    dot_character = models.CharField(max_length=8, default='O')
    modifier_character = models.CharField(max_length=8, default='Õ')

class TraitListName(models.Model):
    name = models.CharField(max_length=128, unique=True)
    slug = models.SlugField()

    def __unicode__(self):
        return self.name

class Sheet(models.Model):
    name = models.CharField(max_length=128)
    #traits = models.ManyToManyField(Trait, through='TraitList')
    player = models.ForeignKey(User, related_name='personal_characters')
    #narrator = models.ForeignKey(User, related_name='narrated_characters')
    # TODO Change this to support narrators in and outside of the database?
    narrator = models.CharField(max_length=128, default='', blank=True)
    slug = models.SlugField(max_length=128)
    home_chronicle = models.CharField(max_length=128, default='', blank=True) # Make this refer to a real thing from another app

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

    object_id = models.IntegerField(null=True)
    content_type = models.ForeignKey(ContentType, null=True)
    group = generic.GenericForeignKey("content_type", "object_id")

    uploading = models.BooleanField(default=False)

    class Meta:
        unique_together = (("player", "name"))

    def __unicode__(self):
        return self.name

    def _get_slug(self):
        return " ".join([self.player.username, self.name])

    def get_traitlist(self, name):
        return self.traits.filter(traitlistname__name=name).order_by('order')

    def add_traitlist_properties(self, **kwargs):# name, sorted, atomic, negative, display_preference):
        """Updates the properties of a traitlist"""
        overwrite = kwargs.get('overwrite', True)
        def fix_bool_kwargs(key, kwargs):
            if key in kwargs:
                if isinstance(kwargs[key], basestring):
                    kwargs[key] = True if kwargs[key] == 'yes' else False
        for k in ['sorted', 'atomic', 'negative']:
            fix_bool_kwargs(k, kwargs)
        traitlist_name_obj, tl_created = TraitListName.objects.get_or_create(
                name=kwargs['name'],
                defaults={"slug":slugify(kwargs['name'])})
        del kwargs['name']
        if 'overwrite' in kwargs:
            del kwargs['overwrite']
        n_property, created = self.traitlistproperty_set.get_or_create(
                name=traitlist_name_obj,
                defaults=kwargs)
        if created is False and overwrite is True:
            changed = False
            for key, value in kwargs.iteritems():
                if getattr(n_property, key) != value:
                    changed = True
                    setattr(n_property, key, value)
            if changed:
                n_property.save()

    def get_traitlist_property(self, traitlistname):
        if isinstance(traitlistname, basestring):
            return self.traitlistproperty_set.get(name__name=traitlistname)
        else:
            return self.traitlistproperty_set.get(name=traitlistname)

    def get_traitlist_properties(self):
        return self.traitlistproperty_set.all()

    def get_traits(self, traitlist_name):
        traitlist_name_obj = TraitListName.objects.get(name=traitlist_name)
        return self.traits.filter(traitlistname=traitlist_name_obj)

    def _get_traitlist_name_obj(self, traitlist_name):
        try:
            traitlist_name_obj = TraitListName.objects.get(name=traitlist_name)
        except TraitListName.DoesNotExist:
            traitlist_name_obj = TraitListName.objects.create(name=traitlist_name, slug=slugify(traitlist_name))
        return traitlist_name_obj

    def add_trait(self, traitlist_name, trait_attrs):
        traitlist_name_obj = self._get_traitlist_name_obj(traitlist_name)
        if "order" not in trait_attrs:
            try:
                previous_last_order = self.traits.filter(traitlistname=traitlist_name_obj).only('order').values_list('order', flat=True).order_by('-order')[0]
                trait_attrs['order'] = previous_last_order + 1
            except IndexError:
                trait_attrs['order'] = 0
        self.traits.create(traitlistname=traitlist_name_obj, **trait_attrs)

    def insert_trait(self, traitlist_name, trait_attrs, order):
        for trait in self.traits.filter(order__gte=order):
            trait.order = trait.order + 1
            trait.save()
        trait_attrs['order'] = order
        self.traits.create(traitlistname=self._get_traitlist_name_obj(traitlist_name), **trait_attrs)

    def reorder_traits(self, traitlist_name, trait_names):
        """Reorders a traitlist to match the order given

        Should fail if the list doesn't exactly match having the traits named
        """
        tl = self.get_traitlist(traitlist_name)
        order_mapping = {}
        for i, tn in enumerate(trait_names):
            order_mapping[tn] = i
        for t in tl:
            if t.name not in trait_names:
                raise AttributeError("Reordering traitlist include the same members as the original traitlist. %s not found" % t.name)
            t.order = order_mapping[t.name]

        for t in tl:
            t.save()

    def _cascade_experience_expenditure_change(self, prev_entry, next_entry):
        #print "_cascade_experience_expenditure_change"
        if next_entry is None and prev_entry is None:
            #print "both none"
            # No entries left
            self.experience_unspent = self.experience_earned = 0
            self.save()
            return

        if next_entry is None:
            #print "next none"
            self.experience_unspent = prev_entry.unspent
            self.experience_earned = prev_entry.earned
            self.save()
            return

        try:
            #print "looping up"
            while True:
                self._calculate_earned_unspent_from_last(next_entry, prev_entry)
                next_entry.save()
                #print "next becomes", next_entry
                prev_entry = next_entry
                #print "prev is", next_entry
                next_entry = next_entry.get_next_by_date(sheet=self)
        except ExperienceEntry.DoesNotExist:
            #print "setting experience totals to", prev_entry
            self.experience_unspent = prev_entry.unspent
            self.experience_earned = prev_entry.earned
            self.save()
            return

        raise RuntimeError("Got to an invalid place cascading an experience entry")

    def delete_experience_entry(self, in_entry):
        entry = self.experience_entries.get(id=in_entry.id)
        try:
            prev_entry = entry.get_previous_by_date(sheet=self)
        except ExperienceEntry.DoesNotExist:
            # This means we're the first, so use the normal update method
            prev_entry = None
        try:
            next_entry = entry.get_next_by_date(sheet=self)
        except ExperienceEntry.DoesNotExist:
            # This means we're the last, so prev becomes the canonical view
            next_entry = None

        #print "Deleting entry", entry
        entry.delete()
        self._cascade_experience_expenditure_change(prev_entry, next_entry)

    def edit_experience_entry(self, in_entry):
        entry = self.experience_entries.get(id=in_entry.id)
        try:
            prev_entry = entry.get_previous_by_date(sheet=self)
        except ExperienceEntry.DoesNotExist:
            # This means we're the first, so use the normal update method
            prev_entry = None

        #print "Edited experience entry", entry
        #print "Prev experience entry", prev_entry
        self._cascade_experience_expenditure_change(prev_entry, entry)

    def add_experience_entry(self, entry):
        try:
            last_experience_entry = self.experience_entries.all().reverse()[0]
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
        self.save()

    def _calculate_earned_unspent_from_last(self, entry, previous_entry):
        if previous_entry is None:
            FauxEntry = collections.namedtuple('FauxEntry', 'unspent earned')
            previous_entry = FauxEntry(0, 0)
            #print "No last entry"
        entry.unspent = previous_entry.unspent
        entry.earned = previous_entry.earned
        #print entry.change_type, "->", entry.get_change_type_display()
        #print "previous_entry:", previous_entry
        if 3 == entry.change_type:
            entry.unspent = previous_entry.unspent - entry.change
        elif 0 == entry.change_type:
            entry.unspent = previous_entry.unspent + entry.change
            entry.earned = previous_entry.earned + entry.change
        elif 4 == entry.change_type:
            entry.unspent = previous_entry.unspent + entry.change
        elif 1 == entry.change_type:
            entry.earned = previous_entry.earned - entry.change
        elif 2 == entry.change_type:
            entry.earned = entry.change
        elif 5 == entry.change_type:
            entry.unspent = entry.change
        elif 6:
            pass

    def update_experience_total(self):
        try:
            entries = self.experience_entries.all().order_by('-date')
            self.experience_unspent = entries[0].unspent
            self.experience_earned = entries[0].earned
        except IndexError:
            self.experience_unspent = self.experience_earned = 0

    def add_default_traitlist_properties(self):
        try:
            self.vampiresheet.add_default_traitlist_properties()
        except VampireSheet.DoesNotExist:
            pass

    def safe_delete(self):
        delete_storage_user = User.objects.get(username__startswith='deleted_character_sheets')
        self.player = delete_storage_user
        from datetime import datetime
        self.name = self.name + "||" + unicode(datetime.now())
        self.object_id = None
        self.content_type = None
        self.save()

    def snapshot(self):
        from copy import deepcopy
        copied_obj = deepcopy(self)

        from datetime import datetime
        copied_obj.name = copied_obj.name + "||snapshot" + unicode(datetime.now())
        copied_obj.pk = None
        copied_obj.id = None
        copied_obj.object_id = None
        copied_obj.content_type = None
        copied_obj.save()
        snapshot = Snapshot.objects.create(
            original_sheet = self,
            snapshot_sheet = copied_obj)

        for t in self.traits.all():
            t.sheet_id = copied_obj.id
            t.pk = None
            t.id = None
            t.save()
        for ee in self.experience_entries.all():
            add_ee = ExperienceEntry()
            add_ee.reason =      ee.reason
            add_ee.change =      ee.change
            add_ee.change_type = ee.change_type
            add_ee.earned =      ee.earned
            add_ee.unspent =     ee.unspent
            add_ee.date =        ee.date
            copied_obj.add_experience_entry(add_ee)
        return copied_obj

    def save(self, *args, **kwargs):
        self.slug = slugify(self._get_slug())
        super(Sheet, self).save(*args, **kwargs)

    def get_absolute_url(self, group=None):
        kwargs = {"sheet_slug": self.slug}
        # We check for attachment of a group. This way if the Task object
        # is not attached to the group the application continues to function.
        if group:
            return group.content_bridge.reverse("sheet_list", group, kwargs=kwargs)
        return reverse("sheet_list", kwargs=kwargs)

    def get_recent_expenditures_entry(self):
        entry = ExperienceEntry()
        changed_traits = self.changed_traits.all()#ChangedTrait.objects.filter(sheet=self)
        logging.debug('get_recent_expenditures top %s' % pformat(changed_traits))
        final_reason_str = u''
        changed = []
        removed = []
        noted = []
        renamed = []
        for ct in changed_traits:
            try:
                Trait.objects.get(id=ct.newer_trait_form)
                changed.append(ct)
            except Trait.DoesNotExist:
                removed.append(ct)

        entry.change = 0
        def get_trait_change_display(trait, display_val):
            value_u = u' x' + unicode(display_val) if display_val > 1 else u''
            trait_u = u' (' + trait.note + u')' if trait.show_note() else u''
            return trait.name + value_u + trait_u

        strs = []
        while len(changed) > 0:
            t = changed.pop(0)
            ntf = Trait.objects.get(id=t.newer_trait_form)
            if t.added:
                change_val = ntf.value
            else:
                change_val = ntf.value - t.value
                non_val_differences = False
                if ntf.note != t.note:
                    noted.append((t, ntf))
                    non_val_differences = True
                if ntf.name != t.name:
                    renamed.append((t, ntf))
                    non_val_differences = True
                if non_val_differences and change_val == 0:
                    continue
                if change_val < 0:
                    removed.append(t)
                    continue
            entry.change += change_val
            strs.append(get_trait_change_display(ntf, change_val))
        if len(strs) > 0:
            final_reason_str += u'Purchased '
            final_reason_str += u', '.join(strs)
            final_reason_str += u'. '

        if len(removed) > 0:
            strs = []
            for t in removed:
                try:
                    ntf = Trait.objects.get(id=t.newer_trait_form)
                    change_val = ntf.value - t.value
                except Trait.DoesNotExist:
                    change_val = t.value * -1
                entry.change += change_val
                strs.append(get_trait_change_display(t, abs(change_val)))
            final_reason_str += u'Removed '
            final_reason_str += u', '.join(strs)
            final_reason_str += u'. '

        if len(noted) > 0:
            strs = []
            for orig, new in noted:
                orig.display_preference = 1
                new.display_preference = 10
                strs.append(u'{orig.name} x{orig.value} ({orig.note}) to ({new})'.format(orig=orig, new=new))
            final_reason_str += u'Updated note '
            final_reason_str += u', '.join(strs)
            final_reason_str += u'. '

        if len(renamed) > 0:
            strs = []
            for orig, new in renamed:
                strs.append(u'{orig.name} x{orig.value} ({orig.note}) to {new.name} x{new.value} ({new.note})'.format(orig=orig, new=new))
            final_reason_str += u'Renamed '
            final_reason_str += u', '.join(strs)
            final_reason_str += u'. '

        if entry.change < 0:
            entry.change *= -1
            entry.change_type = 4
        elif entry.change > 0:
            entry.change_type = 3
        else:
            entry.change_type = 6
            
        entry.reason = final_reason_str.strip()
        from datetime import datetime
        entry.date = datetime.now()
        logging.debug('get_recent_expenditures bottom %s' % pformat(changed_traits))
        return entry

class VampireSheet(Sheet):
    nature = models.CharField(max_length=128, blank=True)
    demeanor = models.CharField(max_length=128, blank=True)
    blood = models.PositiveSmallIntegerField(default=10, blank=True)
    clan = models.CharField(max_length=128, blank=True)
    conscience = models.PositiveSmallIntegerField(default=3, blank=True)
    courage = models.PositiveSmallIntegerField(default=3, blank=True)
    generation = models.PositiveSmallIntegerField(default=13, blank=True)
    path = models.CharField(max_length=128, blank=True)
    pathtraits = models.PositiveSmallIntegerField(default=3, blank=True)
    physicalmax = models.PositiveSmallIntegerField(default=10, blank=True)
    sect = models.CharField(max_length=128, default='', blank=True)
    selfcontrol = models.PositiveSmallIntegerField(default=2, blank=True)
    willpower = models.PositiveSmallIntegerField(default=2, blank=True)
    title = models.CharField(max_length=128, blank=True)

    aura = models.SmallIntegerField(default=0, blank=True)
    coterie = models.CharField(max_length=128, default='', blank=True)
    id_text = models.CharField(max_length=128, default='', blank=True)
    sire = models.CharField(max_length=128, default='', blank=True)

    # These need to actually default to whatever value was just set for their permanents
    # Or... better yet... get turned into something that doesn't blow since we have this
    # great uploading framework now!!!
    tempcourage = models.PositiveSmallIntegerField(default=0, blank=True)
    tempselfcontrol = models.PositiveSmallIntegerField(default=0, blank=True)
    tempwillpower = models.PositiveSmallIntegerField(default=0, blank=True)
    tempblood = models.PositiveSmallIntegerField(default=0, blank=True)
    tempconscience = models.PositiveSmallIntegerField(default=0, blank=True)
    temppathtraits = models.PositiveSmallIntegerField(default=0, blank=True)

    def add_default_traitlist_properties(self):
        self.add_traitlist_properties(overwrite=False, name="Physical", sorted=True, display_preference=1)
        self.add_traitlist_properties(overwrite=False, name="Social", sorted=True, display_preference=1)
        self.add_traitlist_properties(overwrite=False, name="Mental", sorted=True, display_preference=1)
        self.add_traitlist_properties(overwrite=False, name="Negative Physical", sorted=True, negative=True, display_preference=1)
        self.add_traitlist_properties(overwrite=False, name="Negative Social", sorted=True, negative=True, display_preference=1)
        self.add_traitlist_properties(overwrite=False, name="Negative Mental", sorted=True, negative=True, display_preference=1)
        self.add_traitlist_properties(overwrite=False, name="Status", sorted=True, display_preference=1)
        self.add_traitlist_properties(overwrite=False, name="Abilities", sorted=True, display_preference=1)
        self.add_traitlist_properties(overwrite=False, name="Influences", sorted=True, display_preference=1)
        self.add_traitlist_properties(overwrite=False, name="Backgrounds", sorted=True, display_preference=1)
        self.add_traitlist_properties(overwrite=False, name="Health Levels", sorted=False, display_preference=1)
        self.add_traitlist_properties(overwrite=False, name="Bonds", sorted=True, display_preference=1)
        self.add_traitlist_properties(overwrite=False, name="Miscellaneous", sorted=False, display_preference=1)
        self.add_traitlist_properties(overwrite=False, name="Derangements", sorted=True, atomic=True, negative=True, display_preference=5)
        self.add_traitlist_properties(overwrite=False, name="Disciplines", sorted=False, atomic=True, display_preference=5)
        self.add_traitlist_properties(overwrite=False, name="Rituals", sorted=False, atomic=True, display_preference=5)
        self.add_traitlist_properties(overwrite=False, name="Merits", sorted=True, atomic=True, display_preference=4)
        self.add_traitlist_properties(overwrite=False, name="Flaws", sorted=True, atomic=True, negative=True, display_preference=4)
        self.add_traitlist_properties(overwrite=False, name="Equipment", sorted=True, display_preference=1)
        self.add_traitlist_properties(overwrite=False, name="Locations", sorted=True, atomic=True, display_preference=5)

class TraitListProperty(models.Model):
    sheet = models.ForeignKey(Sheet)
    name = models.ForeignKey(TraitListName)
    sorted = models.BooleanField(default=True)
    atomic = models.BooleanField(default=False)
    negative = models.BooleanField(default=False)
    display_preference = models.SmallIntegerField(default=1, choices=DISPLAY_PREFERENCES)

    class Meta:
        ordering = ['name__name']
        unique_together = (("sheet", "name"),)
        verbose_name_plural = "trait list properties"

    def __unicode__(self):
        return "%s:%s" % (self.sheet, self.name)

class Formatter():
    def __init__(self,
            name, value, note,
            note_default,
            dot_character,
            display_preference):
        self.name               = name
        self.value              = value
        self.note               = note
        self.note_default       = note_default
        self.dot_character      = dot_character
        self.display_preference = display_preference

    def show_note(self):
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
        show_note = self.show_note()
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

class Trait(models.Model):
    name = models.CharField(max_length=128)
    note = models.CharField(max_length=128, default='', blank=True)
    value = models.IntegerField(default=1)

    display_preference = models.SmallIntegerField(default=1, choices=DISPLAY_PREFERENCES)
    dot_character = models.CharField(max_length=8, default='O')

    approved = models.BooleanField(default=False)

    order = models.PositiveSmallIntegerField()
    sheet = models.ForeignKey(Sheet, related_name='traits')
    traitlistname = models.ForeignKey(TraitListName)

    class Meta:
        ordering = ['order']
        unique_together = (("sheet", "traitlistname", "name"),)

    def show_note(self):
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

    def is_negative(self):
        tlp = TraitListProperty.objects.get(sheet=self.sheet, name=self.traitlistname)
        return tlp.negative

    def __unicode__(self):
        show_note = self.show_note()
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

class ChangedTrait(models.Model):
    sheet = models.ForeignKey(Sheet, related_name='changed_traits')
    date = models.DateTimeField(auto_now_add=True)

    name = models.CharField(max_length=128)
    note = models.CharField(max_length=128, default='', blank=True)
    value = models.IntegerField(default=1)

    traitlistname = models.ForeignKey(TraitListName)

    newer_trait_form = models.PositiveIntegerField(null=True)#models.ForeignKey(Trait, related_name="changes", null=True)
    added = models.BooleanField(default=False)

    class Meta:
        ordering = ['date']

    def show_note(self):
        return self.note != Trait._meta.get_field_by_name('note')[0].get_default()

    def __unicode__(self):
        from pprint import pformat
        return pformat(
        {'sheet': self.sheet.name,
         'date':pformat(self.date),
         'name':self.name,
         'note':self.note,
         'value':self.value,
         'traitlistname':self.traitlistname.name,
         'newer_trait_form':pformat(self.newer_trait_form),
         'added': self.added})

def track_added_trait(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.sheet.uploading:
        return
    create_kwargs = {
        'sheet':         instance.sheet,
        'name':          instance.name,
        'note':          instance.note,
        'value':         instance.value,
        'traitlistname': instance.traitlistname,
        'added': True,
        'newer_trait_form': instance.id
    }
    logging.debug('track_added_trait %s' % pformat(create_kwargs))
    ChangedTrait.objects.create(**create_kwargs)

def track_changed_trait(sender, instance, **kwargs):
    if instance.id is None:
        return
    if instance.sheet.uploading:
        return
    orig_trait = Trait.objects.get(pk=instance.id)
    def no_tracked_changes(l, r):
        attrs = ['name', 'value', 'note']
        attr_results = [getattr(l, attr) == getattr(r, attr) for attr in attrs]
        return all(attr_results)
    if no_tracked_changes(instance, orig_trait):
        return
    old_changed = ChangedTrait.objects.filter(sheet=instance.sheet,
                                              newer_trait_form=instance.id)
    logging.debug('track_changed_trait in')
    if len(old_changed) > 0:
        old_changed = old_changed[0]
        if no_tracked_changes(old_changed, instance):
            logging.debug('track_changed_trait Original trait and instance match, so delete the change history')
            old_changed.delete()
            return
        create_kwargs = {
            'sheet':         old_changed.sheet,
            'name':          old_changed.name,
            'note':          old_changed.note,
            'value':         old_changed.value,
            'traitlistname': old_changed.traitlistname,
            'added':         old_changed.added,
            'newer_trait_form': instance.id
        }
        old_changed.delete()
    else:
        create_kwargs = {
            'sheet': orig_trait.sheet,
            'name': orig_trait.name,
            'note': orig_trait.note,
            'value': orig_trait.value,
            'traitlistname': orig_trait.traitlistname,
            'newer_trait_form': instance.id
        }
    logging.debug('track_changed_trait %s' % pformat(create_kwargs))
    ChangedTrait.objects.create(**create_kwargs)

def track_deleted_trait(sender, instance, **kwargs):
    if instance.sheet.uploading:
        return
    other_inst = ChangedTrait.objects.filter(sheet=instance.sheet,
                                             newer_trait_form=instance.id)

    logging.debug('track_deleted_trait inst %s other_inst %s' % (pformat(instance), pformat(other_inst)))

    if len(other_inst) > 0:
        other_inst = other_inst[0]
        create_delete = not other_inst.added
        create_instance = other_inst
        logging.debug('track_deleted_trait have another inst that was added? %r and creating delete? %r' % (other_inst, create_delete))
    else:
        create_delete = True
        create_instance = instance
        other_inst = None
        logging.debug('track_deleted_trait have no other inst that was added? %r and creating delete? %r' % (other_inst, create_delete))
    if create_delete:
        create_kwargs = {
            'sheet':         create_instance.sheet,
            'name':          create_instance.name,
            'note':          create_instance.note,
            'value':         create_instance.value,
            'traitlistname': create_instance.traitlistname,
            'added': False,
            'newer_trait_form': None
        }
        ChangedTrait.objects.create(**create_kwargs)

    if other_inst is not None:
        other_inst.delete()

models.signals.pre_save.connect(track_changed_trait, Trait)
models.signals.post_save.connect(track_added_trait, Trait)
models.signals.pre_delete.connect(track_deleted_trait, Trait)

CREATURE_TYPES = [
    (0, "Mortal"),
    (1, "Player"),
    (2, "Vampire"),
    (3, "Werewolf"),
    (5, "Changeling"),
    (6, "Wraith"),
    (7, "Mage"),
    (8, "Fera"),
    (9, "Various"),
    (10, "Mummy"),
    (11, "Kuei-Jin"),
    (12, "Hunter"),
    (13, "Demon"),
]

CREATURE_TYPE_TO_NAME = dict(CREATURE_TYPES)
CREATURE_NAME_TO_TYPE = dict((p,l) for l,p in CREATURE_TYPES)

CREATURE_TYPE_SHEET_MAPPING = {
    VampireSheet: "Vampire",
}

class Menu(models.Model):
    name = models.CharField(max_length=128)
    category = models.PositiveSmallIntegerField(choices=CREATURE_TYPES, default=1)
    sorted = models.BooleanField(default=False)
    negative = models.BooleanField(default=False)
    required = models.BooleanField(default=False)
    autonote = models.BooleanField(default=False)
    display_preference = models.PositiveSmallIntegerField(default=0, choices=DISPLAY_PREFERENCES)

    def __unicode__(self):
        return pformat(self.__dict__)

    @classmethod
    def get_menu_for_traitlistname(self, traitlistname, sheet_class=None):
        translations = {
            'Negative Physical': 'Physical, Negative',
            'Negative Social': 'Social, Negative',
            'Negative Mental': 'Mental, Negative',
        }
        lookup_name = traitlistname.name
        if translations.has_key(lookup_name):
            lookup_name = translations[lookup_name]

        if sheet_class is not None:
            try:
                #from pprint import pprint
                #pprint(Menu.objects.filter(category=CREATURE_NAME_TO_TYPE[CREATURE_TYPE_SHEET_MAPPING[sheet_class]]).filter(name__startswith=lookup_name).values_list('name', flat=True))
                return Menu.objects.filter(category=CREATURE_NAME_TO_TYPE[CREATURE_TYPE_SHEET_MAPPING[sheet_class]]).get(name__startswith=lookup_name)
            except Menu.DoesNotExist:
                pass
            except Menu.MultipleObjectsReturned:
                pass
        return Menu.objects.get(name=lookup_name)

class MenuItem(models.Model):
    name = models.CharField(max_length=128)
    cost = models.CharField(max_length=128, default='1', blank=True)
    note = models.CharField(max_length=128, default='', blank=True)
    order = models.PositiveSmallIntegerField()
    parent = models.ForeignKey(Menu)

    item_type = models.PositiveSmallIntegerField(choices=[(0, "item"), (1, "include"), (2, "submenu")])
    menu_to_import = models.ForeignKey(Menu, related_name='imported_menus', null=True)

    class Meta:
        ordering = ["order"]

    def __unicode__(self):
        formatter = Formatter(
            name=self.name,
            value=self.cost,
            note=self.note,
            note_default='',
            dot_character='O',
            display_preference=self.parent.display_preference)
        return formatter.__unicode__()

class FailedUpload(models.Model):
    file = models.FileField(upload_to="failed_uploads/%Y%m%d%H%M%S")
    time = models.DateTimeField(auto_now_add=True)
    player = models.ForeignKey(User, related_name='failed_uploads')
    exception = models.TextField()
    traceback = models.TextField()
    verified = models.BooleanField(default=False)

class Snapshot(models.Model):
    original_sheet = models.ForeignKey(Sheet, related_name="snapshots")
    snapshot_sheet = models.ForeignKey(Sheet, related_name="am_i_a_snapshot")
    datetime = models.DateTimeField(auto_now_add=True)